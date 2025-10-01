# -*- coding: utf-8 -*-
import csv
import unicodedata
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User, Group
from django.db.models import Q

from centro.models import Profesores, Departamentos  # <-- ajusta si tus modelos están en otra app


def norm(s):
    """Normaliza cadena: trim + NFKC; None -> '' y colapsa espacios."""
    if s is None:
        return ""
    s = str(s).strip()
    s = unicodedata.normalize("NFKC", s)
    s = " ".join(s.split())
    return s


def norm_key(s):
    """Normaliza para comparar: lower + norm."""
    return norm(s).lower()


def parse_nombre_apellidos(empleado):
    """Espera 'Apellidos, Nombre'. Si no, apellidos=empleado, nombre=''."""
    empleado = norm(empleado)
    if "," in empleado:
        apellidos, nombre = empleado.split(",", 1)
        return norm(apellidos), norm(nombre)
    return empleado, ""


def limpiar_tel(s):
    """Limpia teléfonos tipo '0' o vacíos."""
    s = norm(s)
    return "" if s in {"0", "000000000"} else s


# === Mapeo EXACTO Puesto -> Departamento (según tabla proporcionada) ===
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
# Diccionario normalizado (keys normalizados)
MAP_PUESTO_TO_DEPARTAMENTO = {norm_key(k): v for k, v in MAP_PUESTO_TO_DEPARTAMENTO_RAW.items()}


def map_departamento_desde_puesto(puesto):
    """
    Devuelve el nombre de Departamento (str) según mapeo exacto de Puesto.
    Si no hay mapeo, devuelve None.
    """
    return MAP_PUESTO_TO_DEPARTAMENTO.get(norm_key(puesto))


def get_departamento_instance(nombre_dept):
    """
    Devuelve (dept_obj, dept_crear).
    - Si nombre_dept es None o '', retorna (None, None).
    - Si existe en BD (por Nombre o Abr, case-insensitive), retorna (dept, None).
    - Si no existe, retorna (None, (Nombre, Abr_sugerida)).
    """
    if not nombre_dept:
        return None, None
    nombre_dept = norm(nombre_dept)

    dept = Departamentos.objects.filter(
        Q(Nombre__iexact=nombre_dept) | Q(Abr__iexact=nombre_dept)
    ).first()
    if dept:
        return dept, None

    sugerida_abr = (
        "".join([p[0].upper() for p in nombre_dept.split() if p[:1].isalpha()])[:4]
        or nombre_dept[:4].upper()
    )
    return None, (nombre_dept, sugerida_abr)


class Command(BaseCommand):
    help = "Importa profesores desde CSV (dry-run): imprime acciones, no modifica BD."

    # Helpers de estilo seguros (compatibles con versiones antiguas)
    def _style(self, name, text):
        sty = getattr(self.style, name, None)
        return sty(text) if sty else text

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Ruta al CSV")

    def _leer_csv(self, csv_path):
        # Intenta utf-8-sig y cae a latin-1 si falla
        try:
            with csv_path.open(newline="", encoding="utf-8-sig") as f:
                return list(csv.DictReader(f))
        except UnicodeDecodeError:
            with csv_path.open(newline="", encoding="latin-1") as f:
                return list(csv.DictReader(f))

    def handle(self, *args, **options):
        csv_path = Path(options["csv_path"])
        if not csv_path.exists():
            raise CommandError(f"CSV no encontrado: {csv_path}")

        rows = self._leer_csv(csv_path)

        # Estructuras para RESUMEN
        departamentos_a_crear = set()   # nombres (canónicos)
        cambios_departamento = []       # [(prof_formateado, antes, despues)]
        nuevas_altas = []               # [prof_formateado]
        csv_claves = set()              # claves (Nombre, Apellidos, DNI) del CSV
        puestos_desconocidos = set()    # puestos no mapeados (normalizados para evitar duplicados)

        # Grupo 'profesor'
        grupo = Group.objects.filter(name="profesor").first()
        if not grupo:
            self.stdout.write(self._style("WARNING", "AVISO: El grupo 'profesor' no existe. Se debería crear."))
            # grupo = Group.objects.create(name="profesor")  # <-- escritura (comentada)

        self.stdout.write(self._style("MIGRATE_HEADING", f"Procesando {len(rows)} filas del CSV (dry-run)"))
        self.stdout.write("")

        for i, row in enumerate(rows, start=1):
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

            # Departamento por mapeo EXACTO proporcionado
            dept_nombre = map_departamento_desde_puesto(puesto)
            if not dept_nombre:
                # AVISO por fila + agregar al resumen final de desconocidos
                puesto_norm = norm(puesto)
                if puesto_norm:
                    if puesto_norm not in puestos_desconocidos:
                        self.stdout.write(self._style("WARNING", f"[!] Puesto NO mapeado: '{puesto_norm}' (empleado: {apellidos}, {nombre})"))
                    puestos_desconocidos.add(puesto_norm)

            dept_obj, dept_crear = get_departamento_instance(dept_nombre)

            # Buscar profesor existente por triple clave
            prof = Profesores.objects.filter(
                Nombre__iexact=nombre,
                Apellidos__iexact=apellidos,
                DNI__iexact=dni,
            ).first()

            # Texto departamento para impresión
            if dept_obj:
                dept_txt = f"Departamento: {dept_obj.Nombre} (id={dept_obj.id})"
            elif dept_crear:
                dept_txt = f"Departamento a crear: '{dept_crear[0]}' (Abr sugerida: '{dept_crear[1]}')"
            else:
                dept_txt = "Departamento: (no determinado)"

            if prof:
                # EXISTE
                self.stdout.write(self._style("SUCCESS", f"[=] EXISTE: {prof.Apellidos}, {prof.Nombre} / DNI {prof.DNI}"))
                cambios = []

                # Datos base
                if norm(prof.Telefono) != telefono:
                    cambios.append(f"Telefono: '{prof.Telefono}' -> '{telefono}'")
                    # prof.Telefono = telefono
                if norm(prof.Movil) != movil:
                    cambios.append(f"Movil: '{prof.Movil}' -> '{movil}'")
                    # prof.Movil = movil
                if email and norm(prof.Email) != email:
                    cambios.append(f"Email: '{prof.Email}' -> '{email}'")
                    # prof.Email = email

                # Departamento
                if dept_obj and prof.Departamento_id != dept_obj.id:
                    cambios.append(f"Departamento: '{prof.Departamento}' -> '{dept_obj}'")
                    cambios_departamento.append(
                        (f"{prof.Apellidos}, {prof.Nombre} (DNI {prof.DNI})", f"{prof.Departamento}", f"{dept_obj.Nombre}")
                    )
                    # prof.Departamento = dept_obj
                elif dept_crear:
                    departamentos_a_crear.add(dept_crear[0])

                # Baja -> False si venía de baja
                if prof.Baja:
                    cambios.append("Baja: True -> False")
                    # prof.Baja = False

                # Usuario
                user_accion = None
                if prof.user:
                    if username and prof.user.username != username:
                        user_accion = f"User.username: '{prof.user.username}' -> '{username}'"
                        # prof.user.username = username; prof.user.save()
                    if grupo and not prof.user.groups.filter(name="profesor").exists():
                        user_accion = (user_accion or "") + (" + añadir a grupo 'profesor'")
                        # prof.user.groups.add(grupo)
                else:
                    if username:
                        user_accion = f"Crear User(username='{username}', password='<DNI>', email='{email}') y vincular"
                        # user = User.objects.create_user(username=username, password=dni or User.objects.make_random_password(), email=email)
                        # if grupo: user.groups.add(grupo)
                        # prof.user = user
                    else:
                        user_accion = "ERROR: No hay 'Usuario IdEA' para crear el User"

                # Imprimir acciones
                if dept_crear:
                    self.stdout.write(self._style("WARNING", f"    {dept_txt}"))
                    self.stdout.write(self._style("SUCCESS", "    # Departamentos.objects.create(Abr='{}', Nombre='{}')".format(dept_crear[1], dept_crear[0])))
                if cambios:
                    for c in cambios:
                        self.stdout.write(f"    - {c}")
                if user_accion:
                    self.stdout.write(f"    - {user_accion}")

                if cambios or user_accion or dept_crear:
                    self.stdout.write(self._style("SUCCESS", "    # prof.save()"))
                else:
                    self.stdout.write(f"    (Sin cambios)  {dept_txt}")

            else:
                # ALTA NUEVA
                nombre_mostrado = f"{apellidos}, {nombre} / DNI {dni or '(vacío)'}"
                nuevas_altas.append(nombre_mostrado)

                self.stdout.write(self._style("MIGRATE_HEADING", f"[+] ALTA: {nombre_mostrado}"))
                if dept_obj:
                    self.stdout.write(f"    {dept_txt}")
                elif dept_crear:
                    departamentos_a_crear.add(dept_crear[0])
                    self.stdout.write(self._style("WARNING", f"    {dept_txt}"))
                    self.stdout.write(self._style("SUCCESS", "    # Departamentos.objects.create(Abr='{}', Nombre='{}')".format(dept_crear[1], dept_crear[0])))
                    # dept_obj = Departamentos.objects.create(Abr=dept_crear[1], Nombre=dept_crear[0])

                # Crear User
                if not username:
                    self.stdout.write(self._style("ERROR", "    ERROR: Sin 'Usuario IdEA' -> no se puede crear User"))
                else:
                    self.stdout.write(f"    - Crear User(username='{username}', password='<DNI>', email='{email}')")
                    if grupo:
                        self.stdout.write("    - Añadir User al grupo 'profesor'")

                # Crear Profesor (imprime)
                self.stdout.write(
                    "    - Crear Profesores(Nombre='{}', Apellidos='{}', DNI='{}', Telefono='{}', Movil='{}', Email='{}', Departamento={})".format(
                        nombre,
                        apellidos,
                        dni,
                        telefono,
                        movil,
                        email,
                        f"'{dept_obj.Nombre}'" if dept_obj else "None"
                    )
                )
                self.stdout.write("    - Vincular Profesor.user = User")
                self.stdout.write(self._style("SUCCESS", "    # user = User.objects.create_user(username=username, password=dni or User.objects.make_random_password(), email=email)"))
                self.stdout.write(self._style("SUCCESS", "    # if grupo: user.groups.add(grupo)"))
                self.stdout.write(self._style("SUCCESS", "    # prof = Profesores.objects.create(Nombre=nombre, Apellidos=apellidos, DNI=dni, Telefono=telefono, Movil=movil, Email=email, Departamento=dept_obj)"))
                self.stdout.write(self._style("SUCCESS", "    # prof.user = user; prof.save()"))

        # --- BAJAS (en BD pero no en CSV) ---
        self.stdout.write("")
        self.stdout.write(self._style("MIGRATE_HEADING", "Profesores a marcar Baja=True (no aparecen en CSV):"))
        to_baja = []
        for prof in Profesores.objects.all():
            clave_bd = (prof.Nombre.lower(), prof.Apellidos.lower(), (prof.DNI or "").upper())
            if clave_bd not in csv_claves and not prof.Baja:
                to_baja.append(prof)

        if not to_baja:
            self.stdout.write("  (Ninguno)")
        else:
            for prof in to_baja:
                self.stdout.write(self._style("WARNING", f"  [-] {prof.Apellidos}, {prof.Nombre} (DNI {prof.DNI}) -> Baja=True"))
                # prof.Baja = True
                # prof.save()

        # --- RESUMEN FINAL ---
        self.stdout.write("")
        self.stdout.write(self._style("MIGRATE_HEADING", "RESUMEN:"))

        # Departamentos a crear (ya canónicos)
        if departamentos_a_crear:
            self.stdout.write(self._style("WARNING", "Departamentos a crear:"))
            for d in sorted(departamentos_a_crear):
                self.stdout.write(f"  - {d}")
        else:
            self.stdout.write("No hay departamentos nuevos que crear.")

        # Cambios de departamento
        if cambios_departamento:
            self.stdout.write(self._style("WARNING", "Profesores con cambio de departamento:"))
            for prof_txt, antes, despues in cambios_departamento:
                self.stdout.write(f"  - {prof_txt}: {antes} -> {despues}")
        else:
            self.stdout.write("No hay profesores que cambien de departamento.")

        # Nuevas altas
        if nuevas_altas:
            self.stdout.write(self._style("SUCCESS", "Nuevas altas (profesores que no existían):"))
            for p in sorted(nuevas_altas):
                self.stdout.write(f"  - {p}")
        else:
            self.stdout.write("No hay nuevas altas.")

        # Bajas (resumen)
        if to_baja:
            self.stdout.write(self._style("WARNING", f"Profes a marcar de baja: {len(to_baja)}"))
        else:
            self.stdout.write("Profes a marcar de baja: 0")

        # Puestos desconocidos (resumen)
        self.stdout.write("")
        if puestos_desconocidos:
            self.stdout.write(self._style("WARNING", "PUESTOS NO MAPEADOS DETECTADOS (revisar y añadir al diccionario):"))
            for p in sorted(puestos_desconocidos):
                self.stdout.write(f"  - {p}")
        else:
            self.stdout.write("Todos los 'Puesto' del CSV están mapeados.")

        self.stdout.write("")
        self.stdout.write(self._style("SUCCESS", "Dry-run completado. No se ha modificado la base de datos."))
