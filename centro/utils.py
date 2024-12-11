import csv
import re
from pathlib import Path
from django.contrib.auth.models import User, Group
from django.core.exceptions import ObjectDoesNotExist

from django.core.management import call_command
from datetime import datetime


def importar_profesores(csv_file_path):
    # Obtener o crear el grupo "profesor"
    from .models import Profesores, Departamentos, Alumnos, Cursos, Niveles, CursoAcademico
    grupo_profesor, _ = Group.objects.get_or_create(name='profesor')

    profesores_existentes_dni = {profesor.DNI: profesor for profesor in Profesores.objects.all() if profesor.DNI}
    profesores_existentes_nombre = {f"{profesor.Nombre} {profesor.Apellidos}": profesor for profesor in Profesores.objects.all()}
    usuarios_existentes = {user.username: user for user in User.objects.all()}

    nuevos_profesores = 0
    profesores_baja = 0
    nuevos_users = 0

    procesados = set()

    with open(csv_file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            nombre_completo = row['Empleado/a']
            nombres = nombre_completo.split(', ')
            apellidos = nombres[0]
            nombre = nombres[1]
            DNI = row['DNI/Pasaporte']
            telefono = row['Teléfono']
            usuario_idea = row['Usuario IdEA']
            email = row['Cuenta Google/Microsoft']


            # Saltar duplicados
            if DNI in procesados or f"{nombre} {apellidos}" in procesados:
                continue
            procesados.add(DNI)
            procesados.add(f"{nombre} {apellidos}")

            # Buscar el departamento si es necesario
            # departamento = Departamentos.objects.get_or_create(nombre=row['Departamento'])[0]
            departamento = None  # Ajustar esto según sea necesario

            profesor = profesores_existentes_dni.get(DNI) or profesores_existentes_nombre.get(f"{nombre} {apellidos}")

            if profesor:
                profesor.Nombre = nombre
                profesor.Apellidos = apellidos
                profesor.Telefono = telefono
                profesor.Email = email
                profesor.Departamento = departamento
                profesor.Baja = False
                profesor.DNI = DNI
                profesor.save()
            else:
                profesor = Profesores(
                    Nombre=nombre,
                    Apellidos=apellidos,
                    Telefono=telefono,
                    Email=email,
                    Departamento=departamento,
                    Baja=False,
                    DNI=DNI
                )
                profesor.save()
                nuevos_profesores += 1

            if usuario_idea in usuarios_existentes:
                user = usuarios_existentes[usuario_idea]
            else:
                user = User.objects.create_user(
                    username=usuario_idea,
                    password=DNI,
                    email=email,
                    is_active=True,
                    is_superuser=False
                )

            # Asociar el usuario al grupo "profesor" si no está ya en él
            if not user.groups.filter(name='profesor').exists():
                user.groups.add(grupo_profesor)
                user.save()

            # Asociar el usuario al profesor
            profesor.user = user
            profesor.save()

    # Marcar profesores no presentes en el CSV como de baja
    for profesor in Profesores.objects.all():
        if profesor.DNI not in procesados and f"{profesor.Nombre} {profesor.Apellidos}" not in procesados:
            profesor.Baja = True
            profesor.save()

            if profesor.user:
                profesor.user.is_active = False
                profesor.user.save()

            profesores_baja += 1

        # Crear o asociar User a los profesores que no están marcados como baja y no tienen usuario asociado
    for profesor in Profesores.objects.filter(Baja=False, user__isnull=True):
        user = User.objects.create_user(
            username=profesor.Email.split('@')[0],  # Asumiendo que el nombre de usuario puede derivarse del email
            password=profesor.DNI,
            email=profesor.Email,
            is_active=True,
            is_superuser=False
        )
        profesor.user = user
        profesor.save()
        nuevos_users += 1

    print(f"Profesores nuevos añadidos: {nuevos_profesores}")
    print(f"Profesores marcados como baja: {profesores_baja}")
    print(f"Profesores antiguos a los que se ha asociado un usuario: {nuevos_users}")




def importar_alumnos(csv_file_path, borrar_alumnos=False):
    from .models import Alumnos, Cursos
    # Vaciar el campo Unidad de todos los alumnos
    Alumnos.objects.update(Unidad=None)

    # Crear diccionarios para buscar alumnos existentes por DNI, NIE o nombre
    alumnos_existentes_dni = {alumno.DNI: alumno for alumno in Alumnos.objects.all() if alumno.DNI}
    alumnos_existentes_nie = {alumno.NIE: alumno for alumno in Alumnos.objects.all() if alumno.NIE}
    alumnos_existentes_nombre = {alumno.Nombre: alumno for alumno in Alumnos.objects.all()}

    # Mapa para procesar y evitar duplicados
    procesados_dni = set()
    procesados_nie = set()
    procesados_nombre = set()
    nuevos_alumnos = 0
    alumnos_actualizados = 0
    alumnos_baja = 0

    def parse_date(date_str):
        return datetime.strptime(date_str, '%d/%m/%Y').date()

    with open(csv_file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            nombre_completo = row['Alumno/a'].strip()
            nie = row['Nº Id. Escolar'] or None  # Puede ser None si está vacío
            dni = row['DNI/Pasaporte'] or None  # Puede ser None si está vacío
            direccion = row['Dirección']
            cod_postal = row['Código postal']
            localidad = row['Localidad de residencia']
            fecha_nacimiento = parse_date(row['Fecha de nacimiento'])
            provincia = row['Provincia de residencia']
            telefono = row['Teléfono']
            telefono_urgencia = row['Teléfono de urgencia']
            email = row['Correo Electrónico']
            unidad = row['Unidad']
            ap1_tutor = row['Primer apellido Primer tutor']
            ap2_tutor = row['Segundo apellido Primer tutor']
            nom_tutor = row['Nombre Primer tutor']
            observaciones = row['Observaciones de la matrícula']

            # Saltar duplicados en el archivo CSV
            if (dni and dni in procesados_dni) or (
                    nie and nie in procesados_nie) or nombre_completo in procesados_nombre:
                print(f"Saltamos a {nombre_completo} por ya procesado")
                continue

            if dni:
                procesados_dni.add(dni)
            if nie:
                procesados_nie.add(nie)
            procesados_nombre.add(nombre_completo)

            # Buscar el curso
            curso_obj = Cursos.objects.filter(Curso=unidad).first()

            # Buscar alumno existente en la base de datos
            alumno = (
                alumnos_existentes_dni.get(dni) or
                alumnos_existentes_nie.get(nie) or
                alumnos_existentes_nombre.get(nombre_completo)
            )

            if alumno:
                # Actualizar campos del alumno existente
                alumno.Nombre = nombre_completo
                alumno.NIE = nie
                alumno.DNI = dni
                alumno.Direccion = direccion
                alumno.CodPostal = cod_postal
                alumno.Localidad = localidad
                alumno.Fecha_nacimiento = fecha_nacimiento
                alumno.Provincia = provincia
                alumno.Telefono1 = telefono
                alumno.Telefono2 = telefono_urgencia
                alumno.email = email
                alumno.Unidad = curso_obj  # Asignar el curso
                alumno.Ap1tutor = ap1_tutor
                alumno.Ap2tutor = ap2_tutor
                alumno.Nomtutor = nom_tutor
                alumno.Obs = observaciones
                alumno.save()
                alumnos_actualizados += 1
            else:
                # Crear nuevo alumno
                alumno = Alumnos(
                    Nombre=nombre_completo,
                    NIE=nie,
                    DNI=dni,
                    Direccion=direccion,
                    CodPostal=cod_postal,
                    Localidad=localidad,
                    Fecha_nacimiento=fecha_nacimiento,
                    Provincia=provincia,
                    Unidad=curso_obj,
                    Ap1tutor=ap1_tutor,
                    Ap2tutor=ap2_tutor,
                    Nomtutor=nom_tutor,
                    Telefono1=telefono,
                    Telefono2=telefono_urgencia,
                    email=email,
                    Obs=observaciones
                )
                alumno.save()
                nuevos_alumnos += 1
    '''
    if borrar_alumnos:
        # Lógica de borrado opcional
        for alumno in Alumnos.objects.all():
            if alumno.DNI not in procesados_dni and alumno.NIE not in procesados_nie and alumno.Nombre not in procesados_nombre:
                alumno.delete()
                alumnos_baja += 1
    else:
        for alumno in Alumnos.objects.all():
            if alumno.DNI not in procesados_dni and alumno.NIE not in procesados_nie and alumno.Nombre not in procesados_nombre:
                alumno.Unidad = None  # Vaciar la unidad
                alumno.save()
                alumnos_baja += 1
    '''
    for alumno in Alumnos.objects.all():
        if alumno.DNI not in procesados_dni and alumno.NIE not in procesados_nie and alumno.Nombre not in procesados_nombre:
            alumno.Unidad = None  # Vaciar la unidad
            alumno.save()
            alumnos_baja += 1

    print(f"Alumnos actualizados: {alumnos_actualizados}")
    print(f"Alumnos nuevos añadidos: {nuevos_alumnos}")
    print(f"Alumnos marcados como baja: {alumnos_baja}")


def importar_cursos(csv_file_path, csv_file_path2):
    from .models import Profesores, Alumnos, Cursos, Niveles
    # Elimina todas las relaciones ManyToMany existentes
    for curso in Cursos.objects.all():
        curso.EquipoEducativo.clear()

    # Vaciar el campo Unidad de todos los alumnos
    Alumnos.objects.update(Unidad=None)

    # Vaciar tabla de cursos
    Cursos.objects.all().delete()


    # Cargar niveles existentes en un diccionario
    niveles_existentes = {nivel.Nombre: nivel for nivel in Niveles.objects.all()}
    cursos_existentes = {curso.Curso: curso for curso in Cursos.objects.all()}

    nuevos_cursos = 0
    errores_asignacion_nivel = 0
    cursos_sin_tutor = []

    with open(csv_file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            curso_nombre = row['Unidad']
            tutor_info = row['Tutor/a']
            nivel_nombre = row['Curso']

            # Buscar el nivel correspondiente
            nivel = niveles_existentes.get(nivel_nombre)

            # Procesar tutores
            tutor = None
            for tutor_info_segment in extract_tutors_info(tutor_info):
                tutor_name = tutor_info_segment['name']
                tutor_start_date = tutor_info_segment['start_date']
                tutor_end_date = tutor_info_segment['end_date']

                # Buscar el tutor por nombre y apellidos solo si la fecha de inicio es '01/09/YYYY'
                if tutor_start_date.startswith('01/09'):

                    apellidos, nombre = split_full_name(tutor_name)

                    tutor = Profesores.objects.filter(
                        Nombre=nombre,
                        Apellidos=apellidos
                    ).first()
                    if tutor:
                        break


            curso = Cursos(
                Curso=curso_nombre,
                Tutor=tutor,
                Nivel=nivel,
                Abe='',
                Aula=None,  # Dejar vacíos los campos no especificados
            )
            curso.save()
            nuevos_cursos += 1

            # Registrar cursos sin tutor asignado
            if not tutor:
                cursos_sin_tutor.append(curso_nombre)

            if not nivel:
                print(f"Error: No se encontró el nivel '{nivel_nombre}' para el curso: {curso_nombre}")
                errores_asignacion_nivel += 1

    print(f"Cursos nuevos añadidos: {nuevos_cursos}")
    print(f"Errores de asignación de nivel: {errores_asignacion_nivel}")

    # Imprimir listado de cursos sin tutor
    if cursos_sin_tutor:
        print("Cursos sin tutor asignado:")
        for curso in cursos_sin_tutor:
            print(f"- {curso}")

    # Asignar Equipo Educativo
    #asignar_equipo_educativo_seneca(csv_file_path2)

    asignar_equipo_educativo_calculohoras(csv_file_path2)




def extract_tutors_info(tutor_info):
    # Expresión regular para buscar el patrón de nombre y fechas
    pattern = re.compile(r'([^,]+, [^()]+) \((\d{2}/\d{2}/\d{4})-(\d{2}/\d{2}/\d{4})\)')

    # Encuentra todas las coincidencias en la cadena
    matches = pattern.findall(tutor_info)

    # Extrae la información en formato deseado
    tutors = [{'name': match[0].strip(), 'start_date': match[1], 'end_date': match[2]} for match in matches]

    return tutors


def split_full_name(tutor_name):
    # Dividir la cadena en apellidos y nombre usando la coma como separador
    parts = tutor_name.split(',')

    if len(parts) == 2:
        # Apellidos y nombre están en partes[0] y partes[1], respectivamente
        apellidos = parts[0].strip()
        nombre = parts[1].strip()
        return apellidos, nombre
    else:
        # Manejar casos inesperados
        raise ValueError(f"Nombre completo no está en el formato esperado: {tutor_name}")


def asignar_equipo_educativo_seneca(csv_file_path):
    from .models import Profesores, Cursos
    with open(csv_file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            curso_nombre = row['Unidad']
            profesor_info = row['Profesor/a']

            # Dividir el nombre completo en apellidos y nombre
            try:
                apellidos, nombre = split_full_name(profesor_info)
            except ValueError as e:
                print(f"Error al procesar el nombre del profesor: {e}")
                continue

            # Buscar el curso y el profesor
            curso = Cursos.objects.filter(Curso=curso_nombre).first()
            profesor = Profesores.objects.filter(Nombre=nombre, Apellidos=apellidos).first()

            if curso and profesor:
                # Verificar si el profesor ya está asignado al equipo educativo
                if not curso.EquipoEducativo.filter(id=profesor.id).exists():
                    curso.EquipoEducativo.add(profesor)
                    curso.save()
                else:
                    print(f"El profesor '{profesor_info}' ya está asignado al curso '{curso_nombre}'.")
            else:
                if not curso:
                    print(f"Error: No se encontró el curso '{curso_nombre}'")
                if not profesor:
                    print(f"Error: No se encontró el profesor '{profesor_info}'")

    print("Asignación de Equipo Educativo completada.")


def asignar_equipo_educativo_calculohoras(csv_file_path):
    from .models import Profesores, Cursos
    with open(csv_file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        for row in reader:
            curso_nivel = row['Curso']
            unidad_letra = row['Grupo']
            curso_nombre = curso_nivel + " " + unidad_letra
            profesor_info = row['Asignado a']

            # Dividir el nombre completo en apellidos y nombre
            try:
                apellidos, nombre = split_full_name(profesor_info)
            except ValueError as e:
                print(f"Error al procesar el nombre del profesor: {e}")
                continue

            # Buscar el curso y el profesor
            curso = Cursos.objects.filter(Curso=curso_nombre).first()
            profesor = Profesores.objects.filter(Nombre=nombre, Apellidos=apellidos).first()

            if curso and profesor:
                # Verificar si el profesor ya está asignado al equipo educativo
                if not curso.EquipoEducativo.filter(id=profesor.id).exists():
                    curso.EquipoEducativo.add(profesor)
                    curso.save()
                else:
                    print(f"El profesor '{profesor_info}' ya está asignado al curso '{curso_nombre}'.")
            else:
                if not curso:
                    print(f"Error: No se encontró el curso '{curso_nombre}'")
                if not profesor:
                    print(f"Error: No se encontró el profesor '{profesor_info}'")

    print("Asignación de Equipo Educativo completada.")


def asignar_curso_academico(cursoacademico_id):
    # Actualizar AbsentismoActuaciones
    from absentismo.models import Actuaciones, ProtocoloAbs
    from convivencia.models import Amonestaciones, Sanciones
    from reservas.models import Reservas
    from tde.models import IncidenciasTic
    Actuaciones.objects.filter(curso_academico_id__isnull=True).update(curso_academico_id=cursoacademico_id)

    # Actualizar AbsentismoProtocolabs
    ProtocoloAbs.objects.filter(curso_academico_id__isnull=True).update(curso_academico_id=cursoacademico_id)

    # Actualizar ConvivenciaAmonestaciones
    Amonestaciones.objects.filter(curso_academico_id__isnull=True).update(curso_academico_id=cursoacademico_id)

    # Actualizar ConvivenciaSanciones
    Sanciones.objects.filter(curso_academico_id__isnull=True).update(curso_academico_id=cursoacademico_id)

    # Actualizar ReservasReservas
    Reservas.objects.filter(curso_academico_id__isnull=True).update(curso_academico_id=cursoacademico_id)

    # Actualizar TdeIncidenciasTic
    IncidenciasTic.objects.filter(curso_academico_id__isnull=True).update(curso_academico_id=cursoacademico_id)

    print(f"Se ha asignado el curso académico {cursoacademico_id} a todas las tablas.")

def asignar_superusuario(username):
    # Verificar si el usuario 'jefe1' existe
    usuario = User.objects.get(username=username)


    # Asignar el usuario como superusuario si no lo es
    if usuario and not usuario.is_superuser:
        usuario.is_superuser = True
        usuario.is_staff = True  # Asegúrate también de que sea staff si necesita acceso al admin
        usuario.save()
        print("El usuario '{username}' ha sido asignado como superusuario.")


def crear_grupo(groupname):
    # Verificar si el grupo existe
    grupo, creado = Group.objects.get_or_create(name=groupname)

    if creado:
        print(f'Se ha creado el grupo "{groupname}".')
    else:
        print(f'El grupo "{groupname}" ya existe.')


def asignar_grupo(username, groupname):
    # Verificar si el usuario existe
    usuario = User.objects.get(username=username)
    grupo = Group.objects.get(name=groupname)

    if usuario and grupo:
        usuario.groups.add(grupo)
    else:
        print("No se ha podido asignar el grupo '{groupname}' al usuario '{username}'")



def get_current_academic_year():
    """
    Devuelve el objeto CursoAcademico que representa el curso académico actual.
    """
    from .models import CursoAcademico
    today = datetime.now()

    if today.month >= 9:  # Si estamos en septiembre o después
        curso_academico_actual = CursoAcademico.objects.get(año_inicio=today.year)
    else:  # Si estamos antes de septiembre, el curso académico actual comenzó el año anterior
        curso_academico_actual = CursoAcademico.objects.get(año_inicio=today.year - 1)

    return curso_academico_actual

def get_previous_academic_years():
    from .models import CursoAcademico
    current_year = get_current_academic_year()
    previous_years = CursoAcademico.objects.filter(año_inicio__lt=current_year.año_inicio).order_by('-año_inicio')
    return previous_years