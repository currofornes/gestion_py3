# -*- coding: utf-8 -*-
import csv
import unicodedata
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User, Group
from django.db import transaction
from django.db.models import Q

from centro.models import Profesores, Departamentos  # <-- ajusta si es otra app


# -----------------------
# Utilidades de limpieza
# -----------------------
def norm(s):
    """Trim + NFKC + colapsa espacios. None -> ''"""
    if s is None:
        return ""
    s = str(s).strip()
    s = unicodedata.normalize("NFKC", s)
    return " ".join(s.split())


def norm_key(s):
    """Clave normalizada para dicts: lower + norm."""
    return norm(s).lower()


def parse_nombre_apellidos(empleado):
    """Espera 'Apellidos, Nombre'. Si no, apellidos=empleado."""
    empleado = norm(empleado)
    if "," in empleado:
        apellidos, nombre = empleado.split(",", 1)
        return norm(apellidos), norm(nombre)
    return empleado, ""


def limpiar_tel(s):
    s = norm(s)
    return "" if s in {"0", "000000000"} else s


# -----------------------
# Mapeo Puesto -> Dpto (tabla que nos pasaste)
# -----------------------
MAP_PUESTO_TO_DEPARTAMENTO_RAW = {
    "Apoyo al Area Científica o Tecnología": "Orientación",
    "Area Lengua y CC. Sociales (Z.T.S.)": "Orientación",
    "Biología y Geología (Inglés) P.E.S.": "Biología y Geología",
    "Biología y Geología P.E.S.": "Biología y Geología",
    "Dibujo P.E.S.": "Dibujo",
    "Economía P.E.S.": "FOL y Economía",
    "Educación Física (Inglés) P.E.S.": "Educación Física",
    "Educación Física (Secundaria) Inglés": "Educación Física",
    "Filosofía (Inglés) P.E.S.": "Filosofía",
    "Física y Química P.E.S.": "Física y Química",
    "Formación y Orientación Laboral P.E.S.": "FOL y Economía",
    "Francés P.E.S.": "Francés",
    "Frances P.E.S.": "Francés",
    "Geografía e Historia (Inglés) P.E.S.": "Geografía e Historia",
    "Geografía e Historia P.E.S.": "Geografía e Historia",
    "Informática P.E.S.": "Informática",
    "Inglés P.E.S.": "Inglés",
    "Latín P.E.S.": "Latín",
    "Lengua Castellana y Literatura P.E.S.": "Lengua",
    "Matemáticas (Inglés) P.E.S.": "Matemáticas",
    "Matemáticas P.E.S.": "Matemáticas",
    "Música (Inglés) P.E.S.": "Música",
    "Orientación Educativa (Z.T.S.)": "Orientación",
    "Orientación Educativa P.E.S.": "Orientación",
    "Pedagogía Terapeutica Eso": "Orientación",
    "Sistemas y Aplic. Informáticos": "Informática",
    "Tecnología (Inglés) P.E.S.": "Tecnología",
    "Tecnología P.E.S.": "Tecnología",
}
MAP_PUESTO_TO_DEPARTAMENTO = {norm_key(k): v for k, v in MAP_PUESTO_TO_DEPARTAMENTO_RAW.items()}


def map_departamento_desde_puesto(puesto):
    return MAP_PUESTO_TO_DEPARTAMENTO.get(norm_key(puesto))


# -----------------------
# Acceso/creación Dptos
# -----------------------
def get_or_create_departamento(nombre_dept):
    """
    Busca Departamentos por Nombre/Abr (case-insensitive).
    Si no existe, lo crea con Abr sugerida.
    Devuelve (dept_obj, creado_bool).
    """
    if not nombre_dept:
        return None, False
    nombre_dept = norm(nombre_dept)
    dept = Departamentos.objects.filter(Q(Nombre__iexact=nombre_dept) | Q(Abr__iexact=nombre_dept)).first()
    if dept:
        return dept, False
    abr = "".join([p[0].upper() for p in nombre_dept.split() if p[:1].isalpha()])[:4] or nombre_dept[:4].upper()
    dept = Departamentos.objects.create(Nombre=nombre_dept, Abr=abr)
    return dept, True


# -----------------------
# Command
# -----------------------
class Command(BaseCommand):
    help = "Importa profesores desde CSV: crea/actualiza Profesores y Users, marca bajas, y asigna Departamentos."

    def _style(self, name, text):
        sty = getattr(self.style, name, None)
        return sty(text) if sty else text

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Ruta al CSV")

    def _leer_csv(self, csv_path):
        # utf-8-sig -> latin-1
        try:
            with csv_path.open(newline="", encoding="utf-8-sig") as f:
                return list(csv.DictReader(f))
        except UnicodeDecodeError:
            with csv_path.open(newline="", encoding="latin-1") as f:
                return list(csv.DictReader(f))

    @transaction.atomic
    def handle(self, *args, **options):
        csv_path = Path(options["csv_path"])
        if not csv_path.exists():
            raise CommandError(f"CSV no encontrado: {csv_path}")

        rows = self._leer_csv(csv_path)

        # Resumen
        created_prof, updated_prof, dept_changes = [], [], []
        marked_baja, created_depts, created_users = [], [], []
        linked_users, user_conflicts = [], []   # <- corregido
        unknown_positions = set()

        # Grupo 'profesor'
        grupo, _ = Group.objects.get_or_create(name="profesor")

        self.stdout.write(self._style("MIGRATE_HEADING", f"Procesando {len(rows)} filas del CSV"))
        self.stdout.write("")

        # Claves vistas en CSV para luego marcar bajas
        csv_claves = set()

        for row in rows:
            empleado = row.get("Empleado/a", "")
            dni = norm(row.get("DNI/Pasaporte", ""))
            puesto = row.get("Puesto", "")
            telefono = limpiar_tel(row.get("Teléfono", ""))
            movil = limpiar_tel(row.get("Móvil avisos de emergencia", ""))
            username = norm(row.get("Usuario IdEA", ""))
            email = norm(row.get("Cuenta Google/Microsoft", "")) or (f"{username}@example.com" if username else "")

            apellidos, nombre = parse_nombre_apellidos(empleado)
            clave_csv = (nombre.lower(), apellidos.lower(), dni.upper())
            csv_claves.add(clave_csv)

            # Departamento (mapeo exacto)
            dept_nombre = map_departamento_desde_puesto(puesto)
            if not dept_nombre:
                pos_norm = norm(puesto)
                if pos_norm:
                    unknown_positions.add(pos_norm)
                dept_obj = None
                dept_creado = False
            else:
                dept_obj, dept_creado = get_or_create_departamento(dept_nombre)
                if dept_creado:
                    created_depts.append(f"{dept_obj.Nombre} (Abr={dept_obj.Abr})")

            # Buscar profesor existente (no duplicar)
            prof = Profesores.objects.filter(
                Nombre__iexact=nombre,
                Apellidos__iexact=apellidos,
                DNI__iexact=dni,
            ).first()

            # USER: preparar/recuperar sin duplicar
            user_obj = None
            if username:
                user_obj = User.objects.filter(username__iexact=username).first()
                if not user_obj:
                    pwd = dni or User.objects.make_random_password()
                    user_obj = User.objects.create_user(username=username, password=pwd, email=email)
                    created_users.append(username)
                else:
                    if email and norm(user_obj.email) != email:
                        user_obj.email = email
                        user_obj.save()

                # Añadir al grupo 'profesor' si no está
                if not user_obj.groups.filter(name="profesor").exists():
                    user_obj.groups.add(grupo)

            # Crear / actualizar Profesor
            if prof:
                cambios = []
                if norm(prof.Telefono) != telefono:
                    prof.Telefono = telefono
                    cambios.append("Telefono")
                if norm(prof.Movil) != movil:
                    prof.Movil = movil
                    cambios.append("Movil")
                if email and norm(prof.Email) != email:
                    prof.Email = email
                    cambios.append("Email")
                if dept_obj and prof.Departamento_id != dept_obj.id:
                    dept_changes.append(f"{prof.Apellidos}, {prof.Nombre} (DNI {prof.DNI}): {prof.Departamento} -> {dept_obj.Nombre}")
                    prof.Departamento = dept_obj
                    cambios.append("Departamento")
                if prof.Baja:
                    prof.Baja = False
                    cambios.append("Baja=False")

                # Vincular user con control de duplicado
                if user_obj:
                    if prof.user_id:
                        if prof.user.username != user_obj.username:
                            # ¿el user deseado ya pertenece a otro profesor?
                            if hasattr(user_obj, "profesor") and user_obj.profesor and user_obj.profesor.id != prof.id:
                                user_conflicts.append(
                                    f"Conflicto de usuario: '{user_obj.username}' ya vinculado a {user_obj.profesor.Apellidos}, {user_obj.profesor.Nombre}."
                                )
                            else:
                                # Solo renombramos si no existe otro con ese username exacto
                                other = User.objects.filter(username=username).exclude(id=prof.user_id).first()
                                if other:
                                    user_conflicts.append(
                                        f"No se puede cambiar username de {prof.user.username} a '{username}' (ya existe)."
                                    )
                                else:
                                    prof.user.username = username
                                    prof.user.save()
                                    cambios.append("User.username")
                    else:
                        if hasattr(user_obj, "profesor") and user_obj.profesor and user_obj.profesor.id != prof.id:
                            user_conflicts.append(
                                f"Usuario '{user_obj.username}' ya vinculado a {user_obj.profesor.Apellidos}, {user_obj.profesor.Nombre}. No se reasigna."
                            )
                        else:
                            prof.user = user_obj
                            prof.save()
                            linked_users.append(f"{prof.Apellidos}, {prof.Nombre} -> {user_obj.username}")
                            cambios.append("Vincular user")

                if cambios:
                    prof.save()
                    updated_prof.append(f"{prof.Apellidos}, {prof.Nombre} (DNI {prof.DNI}) [{', '.join(cambios)}]")

            else:
                # Crear profesor nuevo
                prof = Profesores(
                    Nombre=nombre,
                    Apellidos=apellidos,
                    DNI=dni,
                    Telefono=telefono,
                    Movil=movil,
                    Email=email,
                    Departamento=dept_obj if dept_obj else None,
                    Baja=False,
                )
                prof.save()
                if user_obj:
                    if hasattr(user_obj, "profesor") and user_obj.profesor:
                        user_conflicts.append(
                            f"Usuario '{user_obj.username}' ya vinculado a {user_obj.profesor.Apellidos}, {user_obj.profesor.Nombre}. No se vincula a {apellidos}, {nombre}."
                        )
                    else:
                        prof.user = user_obj
                        prof.save()
                        linked_users.append(f"{prof.Apellidos}, {prof.Nombre} -> {user_obj.username}")

                created_prof.append(f"{prof.Apellidos}, {prof.Nombre} (DNI {prof.DNI})")

        # Marcar BAJA a quienes no estén en el CSV
        for prof in Profesores.objects.all():
            clave_bd = (prof.Nombre.lower(), prof.Apellidos.lower(), (prof.DNI or "").upper())
            if clave_bd not in csv_claves and not prof.Baja:
                prof.Baja = True
                prof.save()
                marked_baja.append(f"{prof.Apellidos}, {prof.Nombre} (DNI {prof.DNI})")

        # -----------------------
        # RESUMEN
        # -----------------------
        self.stdout.write("")
        self.stdout.write(self._style("MIGRATE_HEADING", "RESUMEN:"))

        if created_depts:
            self.stdout.write(self._style("WARNING", "Departamentos creados:"))
            for d in sorted(created_depts):
                self.stdout.write(f"  - {d}")
        else:
            self.stdout.write("No se han creado departamentos.")

        if dept_changes:
            self.stdout.write(self._style("WARNING", "Cambios de departamento:"))
            for c in dept_changes:
                self.stdout.write(f"  - {c}")
        else:
            self.stdout.write("Sin cambios de departamento.")

        if created_users:
            self.stdout.write(self._style("SUCCESS", "Usuarios creados:"))
            for u in sorted(created_users):
                self.stdout.write(f"  - {u}")
        else:
            self.stdout.write("No se han creado usuarios nuevos.")

        if linked_users:
            self.stdout.write(self._style("SUCCESS", "Vinculaciones Profesor ↔ User:"))
            for l in sorted(linked_users):
                self.stdout.write(f"  - {l}")
        else:
            self.stdout.write("No hay nuevas vinculaciones Profesor ↔ User.")

        if created_prof:
            self.stdout.write(self._style("SUCCESS", "Altas de profesores:"))
            for p in sorted(created_prof):
                self.stdout.write(f"  - {p}")
        else:
            self.stdout.write("No hay altas de profesores.")

        if updated_prof:
            self.stdout.write(self._style("SUCCESS", "Profesores actualizados:"))
            for p in sorted(updated_prof):
                self.stdout.write(f"  - {p}")
        else:
            self.stdout.write("No hay profesores actualizados.")

        if marked_baja:
            self.stdout.write(self._style("WARNING", "Profesores marcados de baja:"))
            for p in sorted(marked_baja):
                self.stdout.write(f"  - {p}")
        else:
            self.stdout.write("No hay profesores marcados de baja.")

        if user_conflicts:
            self.stdout.write("")
            self.stdout.write(self._style("WARNING", "Conflictos de usuario detectados (no se ha duplicado nada):"))
            for c in user_conflicts:
                self.stdout.write(f"  - {c}")

        self.stdout.write("")
        if unknown_positions:
            self.stdout.write(self._style("WARNING", "PUESTOS NO MAPEADOS (añade al diccionario si procede):"))
            for p in sorted(unknown_positions):
                self.stdout.write(f"  - {p}")
        else:
            self.stdout.write("Todos los 'Puesto' del CSV están mapeados.")

        self.stdout.write("")
        self.stdout.write(self._style("SUCCESS", "Importación completada."))
