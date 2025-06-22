import csv
import io
import os
import time
from collections import defaultdict

import unicodedata
from django.contrib import messages
from django.db.models import Q, Count
from django.forms import modelformset_factory
from django.http import HttpResponseForbidden, FileResponse, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.timezone import now

from centro.models import Alumnos, Cursos, Departamentos, Profesores, Niveles, Materia, MateriaImpartida, \
    MatriculaMateria, LibroTexto, MomentoRevisionLibros, RevisionLibroAlumno, EstadoLibro, RevisionLibro
from centro.utils import get_current_academic_year, get_previous_academic_years
from convivencia.models import Amonestaciones, Sanciones
from centro.forms import UnidadForm, DepartamentosForm, UnidadProfeForm, UnidadesProfeForm, SeleccionRevisionForm, \
    RevisionLibroAlumnoForm, SeleccionRevisionProfeForm
from datetime import datetime, timedelta

from gestion import settings


def group_check_je(user):
    return user.groups.filter(name__in=['jefatura de estudios'])

# Curro Jul 24
def group_check_je(user):
    return user.groups.filter(name__in=['jefatura de estudios'])


def group_check_tde(user):
    return user.groups.filter(name__in=['jefatura de estudios', 'tde']).exists()

def group_check_prof(user):
    return user.groups.filter(name__in=['jefatura de estudios', 'profesor']).exists()

def group_check_prof_or_guardia(user):
    return user.groups.filter(name__in=['jefatura de estudios', 'profesor', 'guardia']).exists()

def group_check_prof_and_tutor(user):
    return group_check_prof(user) and is_tutor(user)

def group_check_prof_and_tutor_or_je(user):
    return group_check_prof_and_tutor(user) or group_check_je(user)

def group_check_je_or_orientacion(user):
    return user.groups.filter(name__in=['jefatura de estudios', 'orientacion']).exists()

def group_check_prof_and_tutor_or_je_or_orientacion(user):
    return group_check_prof_and_tutor(user) or group_check_je_or_orientacion(user)

def is_tutor(user):
    # Comprueba si el usuario tiene un perfil de profesor asociado
    if hasattr(user, 'profesor'):
        profesor = user.profesor
        # Comprueba si el profesor es tutor de algún curso
        return Cursos.objects.filter(Tutor_id=profesor.id).exists()

    return False

# Create your views here.


@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
def alumnos(request):
    if request.method == 'POST':
        primer_id = request.POST.get("Unidad")
    else:
        try:
            primer_id = request.session.get('Unidad', Cursos.objects.order_by('Curso').first().id)
        except:
            primer_id = 0

    request.session['Unidad'] = primer_id

    lista_alumnos = Alumnos.objects.filter(Unidad__id=primer_id)
    lista_alumnos = sorted(lista_alumnos, key=lambda d: d.Nombre)
    ids = [{"id": elem.id} for elem in lista_alumnos]

    form = UnidadForm({'Unidad': primer_id})
    lista = zip(lista_alumnos, ContarFaltas(ids), ContarFaltasHistorico(ids), EstaSancionado(ids))
    try:
        context = {'alumnos': lista, 'form': form, 'curso': Cursos.objects.get(id=primer_id), 'menu_convivencia': True}
    except:
        context = {'alumnos': lista, 'form': form, 'curso': None, 'menu_convivencia': True}
    return render(request, 'alumnos.html', context)


@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
def alumnos_curso(request, curso):
    request.POST = request.POST.copy()
    request.POST["Unidad"] = curso
    request.method = "POST"
    return alumnos(request)


@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
def profesores(request):
    if request.method == 'POST':
        dep_id = request.POST.get("Departamento")
        area_id = request.POST.get("Areas")
        if area_id != request.session.get("Areas", ""):
            dep_id = ""
    else:
        dep_id = request.session.get('Departamento', "")
        area_id = request.session.get("Areas", "")

    request.session['Areas'] = area_id
    request.session['Departamento'] = dep_id
    form = DepartamentosForm({'Areas': area_id, 'Departamento': dep_id})
    if dep_id == "":
        lista_profesores = Profesores.objects.all().order_by("Apellidos")
        departamento = ""
    else:
        lista_profesores = Profesores.objects.filter(Departamento__id=dep_id).order_by("Apellidos")
        departamento = Departamentos.objects.get(id=dep_id).Nombre

    cursos = Tutorias(lista_profesores.values("id"))
    lista = zip(lista_profesores, cursos)
    context = {'profesores': lista, 'form': form, "departamento": departamento, 'menu_profesor': True}
    return render(request, 'profesor.html', context)


@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
def profesores_change(request, codigo, operacion):
    dato = {}
    dato["Baja"] = True if operacion == "on" else False
    Profesores.objects.filter(id=codigo).update(**dato)

    return redirect("/centro/profesores")




def Tutorias(lista_id):
    cursos = []
    for prof in lista_id:
        try:
            cursos.append(Cursos.objects.get(Tutor=prof.values()[0]).Curso)
        except:
            cursos.append("")
    return cursos


def EstaSancionado(lista_id):
    estasancionado = []
    hoy = datetime.now()
    dict = {}
    dict["Fecha_fin__gte"] = hoy
    dict["Fecha__lte"] = hoy
    sanc = Sanciones.objects.filter(**dict).order_by("Fecha")
    listaid = [x.IdAlumno.id for x in sanc]
    for alum in lista_id:
        if list(alum.values())[0] in listaid:
            estasancionado.append(True)
        else:
            estasancionado.append(False)
    return estasancionado


@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
def cursos(request):
    lista_cursos = Cursos.objects.all().order_by("Curso")
    context = {'cursos': lista_cursos, 'menu_cursos': True}
    return render(request, 'cursos.html', context)


# Curro Jul 24: Redefino la vista misalumnos
@login_required(login_url='/')
@user_passes_test(group_check_prof, login_url='/')
def misalumnos(request):
    if not hasattr(request.user, 'profesor'):
        return render(request, 'error.html', {'message': 'No tiene un perfil de profesor asociado.'})

    profesor = request.user.profesor
    cursos = Cursos.objects.filter(EquipoEducativo=profesor)
    cursos_resto = Cursos.objects.exclude(EquipoEducativo=profesor)

    if request.method == 'POST':
        if request.POST.get("FormTrigger") == "Unidad":
            primer_id = request.POST.get("Unidad")
        else:
            primer_id = request.POST.get("UnidadResto")
    else:
        try:
            primer_id = cursos.order_by('Curso').first().id
        except:
            primer_id = 0

    request.session['Unidad'] = primer_id

    lista_alumnos = Alumnos.objects.filter(Unidad__id=primer_id)
    lista_alumnos = sorted(lista_alumnos, key=lambda d: d.Nombre)
    ids = [{"id": elem.id} for elem in lista_alumnos]

    form = UnidadesProfeForm({'Unidad': request.POST.get("Unidad"), 'UnidadResto': request.POST.get("UnidadResto")},
                             profesor=profesor)
    lista = zip(lista_alumnos, ContarFaltas(ids), ContarFaltasHistorico(ids), EstaSancionado(ids))
    try:
        context = {'alumnos': lista, 'form': form, 'curso': Cursos.objects.get(id=primer_id), 'menu_convivencia': True,
                   'profesor': profesor}
    except:
        context = {'alumnos': lista, 'form': form, 'curso': None, 'menu_convivencia': True, 'profesor': profesor}
    return render(request, 'misalumnos.html', context)

@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
def busqueda(request):
    query = ""
    resultados = []
    num_resultados = 0
    tiempo_busqueda = 0

    if request.method == 'POST':
        query = request.POST.get('q')
        if query:
            query_normalizada = normalizar_texto(query)

            # Medir el tiempo de inicio
            start_time = time.time()

            # Realizar la búsqueda
            resultados = Alumnos.objects.all()
            resultados = [
                alumno for alumno in resultados
                if query_normalizada in normalizar_texto(alumno.Nombre) or
                   query_normalizada in (alumno.DNI or '').lower() or
                   query_normalizada in (alumno.NIE or '').lower() or
                   query_normalizada in normalizar_texto(alumno.email)
            ]

            # Medir el tiempo de fin
            end_time = time.time()

            # Calcular el tiempo de búsqueda y redondear a 2 decimales
            tiempo_busqueda = round(end_time - start_time, 2)

            # Número de resultados obtenidos
            num_resultados = len(resultados)

    context = {
        'resultados': resultados,
        'query': query,
        'num_resultados': num_resultados,
        'tiempo_busqueda': tiempo_busqueda,
        'menu_convivencia': True
    }
    return render(request, 'buscar_alumnos.html', context)


def normalizar_texto(texto):
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    return texto.lower()


def ContarFaltas(lista_id):
    curso_academico_actual = get_current_academic_year()

    contar = []
    for alum in lista_id:
        am = str(len(Amonestaciones.objects.filter(IdAlumno_id=list(alum.values())[0], curso_academico=curso_academico_actual)))
        sa = str(len(Sanciones.objects.filter(IdAlumno_id=list(alum.values())[0], curso_academico=curso_academico_actual)))

        contar.append(am + "/" + sa)
    return contar

def ContarFaltasHistorico(lista_id):

    contar = []
    for alum in lista_id:
        am = str(len(Amonestaciones.objects.filter(IdAlumno_id=list(alum.values())[0])))
        sa = str(len(Sanciones.objects.filter(IdAlumno_id=list(alum.values())[0])))

        contar.append(am + "/" + sa)
    return contar


def importar_materias(request: HttpRequest):
    niveles = Niveles.objects.all()

    if request.method == "POST":
        for nivel in niveles:
            file_key = f'csv_nivel_{nivel.id}'
            csv_file = request.FILES.get(file_key)

            if not csv_file:
                continue  # No se ha subido archivo para este nivel

            try:
                csv_reader = decode_file(csv_file)
            except UnicodeDecodeError:
                messages.error(request, f"No se pudo leer el archivo para {nivel.Nombre}. Usa codificación UTF-8.")
                continue

            # Ignorar encabezado
            next(csv_reader, None)

            materias_importadas = 0
            for row in csv_reader:
                if len(row) < 4:
                    continue

                nombre = row[0].strip()
                grupo = row[1].strip()
                abrev = row[2].strip()
                creditos = row[3].strip()
                horas = int(creditos) if creditos.isdigit() else 0

                print(nivel.Nombre)

                materia, created = Materia.objects.update_or_create(
                    nombre=nombre,
                    nivel=nivel,
                    defaults={
                        'abr': abrev,
                        'horas': horas
                    }
                )
                if created:
                    materias_importadas += 1

            messages.success(request, f"Se importaron {materias_importadas} materias para {nivel.Nombre}.")

        return redirect('importar_materias')

    return render(request, "importar_materias.html", {"niveles": niveles})


def decode_file_dict(file):
    """Intenta decodificar el archivo con varias codificaciones comunes."""
    content = file.read()  # Leer todo el archivo como bytes
    for encoding in ['utf-8-sig', 'utf-8', 'latin1']:
        try:
            decoded = content.decode(encoding).splitlines()
            return csv.DictReader(decoded)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("No se pudo leer el archivo con ninguna codificación válida.")

def decode_file(file):
    """Intenta decodificar el archivo con varias codificaciones comunes."""
    content = file.read()  # Leer todo el archivo como bytes
    for encoding in ['utf-8-sig', 'utf-8', 'latin1']:
        try:
            decoded = content.decode(encoding).splitlines()
            return csv.reader(decoded)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("No se pudo leer el archivo con ninguna codificación válida.")


def importar_materias_impartidas(request):
    if request.method == 'POST' and 'csv_materias_impartidas' in request.FILES:
        csv_file = request.FILES['csv_materias_impartidas']

        try:
            csv_reader = decode_file_dict(csv_file)
        except UnicodeDecodeError:
            messages.error(request, f"No se pudo leer el archivo.")
            return redirect('importar_materias_impartidas')

        # Ignorar encabezado
        next(csv_reader, None)


        for row in csv_reader:
            nombre_nivel = row["Curso"].strip()
            nombre_materia = row["Materia"].strip()
            nombre_unidad = row["Unidad"].strip()
            nombre_profesor = row["Profesor/a"].strip()

            # Buscar Nivel
            nivel = Niveles.objects.filter(Nombre__iexact=nombre_nivel).first()
            if not nivel:
                messages.warning(request, f"Nivel no encontrado: {nombre_nivel}")
                continue

            # Buscar Curso (Unidad)
            curso = Cursos.objects.filter(Curso=nombre_unidad, Nivel=nivel).first()
            if not curso:
                messages.warning(request, f"Curso (Unidad) no encontrado: {nombre_unidad} en {nivel.Nombre}")
                continue

            # Buscar Materia
            materia = Materia.objects.filter(nombre=nombre_materia, nivel=nivel).first()
            if not materia:
                messages.warning(request, f"Materia no encontrada: {nombre_materia} en {nivel.Nombre}")
                continue

            # Buscar Profesor
            try:
                apellidos, nombre = [p.strip() for p in nombre_profesor.split(',', 1)]
                nombre_completo_csv = f"{apellidos}, {nombre}"
                normalizado_csv = quitar_tildes(nombre_completo_csv).lower()

                profesor = None
                for prof in Profesores.objects.all():
                    nombre_prof = quitar_tildes(str(prof)).lower()
                    if nombre_prof == normalizado_csv:
                        profesor = prof
                        break

                if not profesor:
                    messages.warning(request, f"Profesor no encontrado: {nombre_profesor}")
                    continue
            except (ValueError, Profesores.DoesNotExist):
                messages.warning(request, f"Profesor no encontrado: {nombre_profesor}")
                continue

            # Crear MateriaImpartida
            obj, created = MateriaImpartida.objects.get_or_create(
                materia=materia,
                curso=curso,
                profesor=profesor
            )
            if created:
                messages.success(request, f"Importada: {materia.nombre} en {curso.Curso} por {profesor}")
            else:
                messages.info(request, f"Ya existía: {materia.nombre} en {curso.Curso} por {profesor}")

        return redirect('importar_materias_impartidas')

    return render(request, 'importar_materias_impartidas.html')

def quitar_tildes(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

def importar_matriculas_materias(request):
    if request.method == "POST" and 'csv_matriculas' in request.FILES:
        nivel = request.POST.get('nivel')
        if not nivel:
            messages.error(request, "Debes seleccionar un nivel.")
            return redirect('importar_matriculas_materias')

        csv_file = request.FILES['csv_matriculas']

        try:
            csv_reader = decode_file(csv_file)
        except UnicodeDecodeError:
            messages.error(request, "No se pudo leer el archivo.")
            return redirect('importar_matriculas_materias')

        encabezado = next(csv_reader)
        materias_csv = encabezado[2:]

        nuevas = []
        existentes = []
        errores = []
        multi_profesores = 0

        cursos_del_nivel = Cursos.objects.filter(Curso__icontains=nivel)
        if not cursos_del_nivel.exists():
            messages.error(request, f"No se encontraron cursos para el nivel '{nivel}'")
            return redirect('importar_matriculas_materias')

        for row_index, row in enumerate(csv_reader, start=2):  # Desde fila 2 por encabezado
            nombre_alumno_csv = quitar_tildes(row[0]).strip().lower()
            nombre_unidad_csv = quitar_tildes(row[1]).strip().lower()

            try:
                curso = cursos_del_nivel.get(Curso__iexact=row[1].strip())
            except Cursos.DoesNotExist:
                errores.append(f"Fila {row_index}: Unidad no encontrada - {row[1]}")
                continue

            alumnos_en_curso = Alumnos.objects.filter(Unidad=curso)
            alumno = next(
                (a for a in alumnos_en_curso if quitar_tildes(a.Nombre).strip().lower() == nombre_alumno_csv),
                None
            )

            if not alumno:
                errores.append(f"Fila {row_index}: Alumno no encontrado - {row[0]}")
                continue

            for i, valor in enumerate(row[2:]):
                if valor.strip().upper() != "MATR":
                    continue

                nombre_materia_csv = quitar_tildes(materias_csv[i]).strip().lower()

                materias_imp = MateriaImpartida.objects.filter(
                    curso=curso,
                    materia__nombre__iexact=materias_csv[i].strip()
                )

                if not materias_imp.exists():
                    errores.append(f"Fila {row_index}: Materia '{materias_csv[i]}' no encontrada en {curso.Curso}")
                    continue

                if materias_imp.count() > 1:
                    multi_profesores += 1

                for materia_imp in materias_imp:
                    matricula, creada = MatriculaMateria.objects.get_or_create(
                        alumno=alumno,
                        materia_impartida=materia_imp
                    )

                    if creada:
                        nuevas.append(f"{alumno.Nombre} → {materia_imp.materia.nombre} ({curso.Curso}) [{materia_imp.profesor}]")
                    else:
                        existentes.append(f"{alumno.Nombre} ya estaba en {materia_imp.materia.nombre} ({curso.Curso}) [{materia_imp.profesor}]")

        resumen = {
            'nuevas': nuevas,
            'existentes': existentes,
            'errores': errores,
            'multi_profesores': multi_profesores,
        }

        return render(request, 'importar_matriculas_materias.html', {'resumen': resumen})

    return render(request, 'importar_matriculas_materias.html')


def ver_matriculas(request):
    cursos = Cursos.objects.all().order_by("Curso")
    datos = []
    curso_seleccionado = None

    if request.method == "POST":
        curso_id = request.POST.get("curso")
        if curso_id:
            curso_seleccionado = Cursos.objects.get(id=curso_id)
            alumnos = curso_seleccionado.alumnos_set.all().order_by("Nombre")

            for alumno in alumnos:
                matriculas = MatriculaMateria.objects.filter(alumno=alumno)
                materias_agrupadas = {}

                for mat in matriculas:
                    nombre_materia = mat.materia_impartida.materia.nombre
                    profesor = str(mat.materia_impartida.profesor)

                    if nombre_materia not in materias_agrupadas:
                        materias_agrupadas[nombre_materia] = set()
                    materias_agrupadas[nombre_materia].add(profesor)

                # Convertir sets a listas para que sean iterables en la template
                materias_agrupadas = {
                    materia: sorted(list(profesores))
                    for materia, profesores in materias_agrupadas.items()
                }

                datos.append({
                    "alumno": alumno,
                    "materias_agrupadas": materias_agrupadas
                })

    return render(request, "ver_matriculas.html", {
        "cursos": cursos,
        "curso_seleccionado": curso_seleccionado,
        "datos": datos
    })

def listar_materias_impartidas(request):
    cursos_disponibles = Cursos.objects.order_by('Nivel__Abr', 'Curso')
    curso_id = request.GET.get('curso')
    registros = MateriaImpartida.objects.select_related('materia', 'curso', 'profesor')

    if curso_id:
        registros = registros.filter(curso_id=curso_id)

    materias_agrupadas = []

    agrupados = defaultdict(list)
    for reg in registros:
        clave = (reg.curso, reg.materia)
        agrupados[clave].append(reg.profesor)

    for (curso, materia), profesores in agrupados.items():
        materias_agrupadas.append({
            'curso': curso,
            'materia': materia,
            'profesores': profesores
        })

    context = {
        'materias_agrupadas': materias_agrupadas,
        'cursos_disponibles': cursos_disponibles,
        'curso_seleccionado': int(curso_id) if curso_id else None
    }
    return render(request, 'listar_materias_impartidas.html', context)

def importar_libros_texto(request):
    if request.method == "POST" and 'csv_libros' in request.FILES:
        nivel_id = request.POST.get('nivel')
        if not nivel_id:
            messages.error(request, "Debes seleccionar un nivel.")
            return redirect('importar_libros_texto')

        csv_file = request.FILES['csv_libros']

        try:
            csv_reader = decode_file(csv_file)
        except UnicodeDecodeError:
            messages.error(request, "No se pudo leer el archivo.")
            return redirect('importar_libros_texto')

        try:
            nivel = Niveles.objects.get(id=nivel_id)
        except Niveles.DoesNotExist:
            messages.error(request, "Nivel no encontrado.")
            return redirect('importar_libros_texto')

        encabezado = next(csv_reader)
        nuevas = []
        errores = []

        materias_nivel = Materia.objects.filter(nivel=nivel)

        for row_index, row in enumerate(csv_reader, start=2):
            nombre_materia_csv = quitar_tildes(row[0]).strip().lower()
            if not nombre_materia_csv:
                continue

            materia = next(
                (m for m in materias_nivel if quitar_tildes(m.nombre).strip().lower() == nombre_materia_csv),
                None
            )

            if not materia:
                errores.append(f"Fila {row_index}: Materia no encontrada - {row[0]}")
                continue

            titulo = row[3].strip()
            if not titulo:
                continue  # Saltar libros sin título

            libro = LibroTexto(
                materia=materia,
                nivel=nivel,
                isbn=row[1].strip(),
                editorial=row[2].strip(),
                titulo=titulo,
                anyo_implantacion=int(row[4]) if row[4].isdigit() else None,
                importe_estimado=float(row[5].replace(',', '.')) if row[5].replace(',', '.').replace('.', '', 1).isdigit() else None,
                es_digital=row[6].strip().lower() == "sí",
                incluir_en_cheque_libro=row[7].strip().lower() == "sí",
                es_otro_material=row[8].strip().lower() == "sí"
            )
            libro.save()
            nuevas.append(f"{materia.nombre} - {libro.titulo or 'Sin título'}")

        return render(request, 'importar_libros_texto.html', {
            'resumen': {
                'nuevos': nuevas,
                'errores': errores,
            },
            'niveles': Niveles.objects.all()
        })

    return render(request, 'importar_libros_texto.html', {
        'niveles': Niveles.objects.all()
    })


def ver_libros_texto(request):
    niveles = Niveles.objects.all()
    libros = []

    nivel_id = request.GET.get('nivel')
    nivel_seleccionado = None

    if nivel_id:
        try:
            nivel_seleccionado = Niveles.objects.get(id=nivel_id)
            libros = LibroTexto.objects.filter(nivel=nivel_seleccionado).select_related('materia').order_by('materia__nombre')
        except Niveles.DoesNotExist:
            nivel_seleccionado = None

    return render(request, 'ver_libros_texto.html', {
        'niveles': niveles,
        'libros': libros,
        'nivel_seleccionado': nivel_seleccionado,
    })

def seleccionar_revision_view(request):
    profesores_qs = Profesores.objects.filter(Baja=False)

    form = SeleccionRevisionForm(
        request.POST or None,
        profesores_qs=profesores_qs,
        materias_qs=Materia.objects.none(),
        libros_qs=LibroTexto.objects.none()
    )

    return render(request, 'seleccion_revision.html', {
        'form': form,
        'momentos': MomentoRevisionLibros.objects.all()
    })


def revisar_libros(request):
    profesor = request.user.profesor


    form = SeleccionRevisionProfeForm(
        request.POST or None,
        profesor=profesor,
        materias_qs=Materia.objects.none(),
        libros_qs=LibroTexto.objects.none()
    )

    return render(request, 'revisar_libros.html', {
        'form': form,
        'profesor': profesor,
        'momentos': MomentoRevisionLibros.objects.all()
    })

def revisar_libros_view(request, profesor_id, momento_id, materia_id, libro_id):
    profesor = get_object_or_404(Profesores, pk=profesor_id)
    momento = get_object_or_404(MomentoRevisionLibros, pk=momento_id)
    materia = get_object_or_404(Materia, pk=materia_id)
    libro = get_object_or_404(LibroTexto, pk=libro_id)

    # Buscar las materias impartidas por ese profesor de esa materia
    materias_impartidas = MateriaImpartida.objects.filter(
        profesor=profesor,
        materia=materia
    )

    # Buscar los alumnos matriculados en esas materias impartidas
    matriculas = MatriculaMateria.objects.filter(
        materia_impartida__in=materias_impartidas
    ).select_related('alumno')

    alumnos = [m.alumno for m in matriculas]

    return render(request, 'revision_libros.html', {
        'profesor': profesor,
        'momento': momento,
        'materia': materia,
        'libro': libro,
        'alumnos': alumnos,
    })

def revision_exitosa_view(request):
    return render(request, 'revision_exitosa.html')



def obtener_materias_ajax(request):
    profesor_id = request.GET.get('profesor_id')
    materias = Materia.objects.filter(materiaimpartida__profesor_id=profesor_id).distinct()
    data = [{'id': m.id, 'nombre': str(m)} for m in materias]
    return JsonResponse(data, safe=False)

def obtener_libros_ajax(request):
    materia_id = request.GET.get('materia_id')
    libros = LibroTexto.objects.filter(materia_id=materia_id)
    data = [{'id': l.id, 'nombre': str(l)} for l in libros]
    return JsonResponse(data, safe=False)


def get_cursos_profesor(request):
    profesor_id = request.GET.get('profesor_id')
    cursos = Cursos.objects.filter(materiaimpartida__profesor_id=profesor_id).distinct()
    data = [{'id': curso.id, 'nombre': str(curso)} for curso in cursos]
    return JsonResponse(data, safe=False)

def get_materias_profesor_curso(request):
    profesor_id = request.GET.get('profesor_id')
    curso_id = request.GET.get('curso_id')
    materias = Materia.objects.filter(materiaimpartida__profesor_id=profesor_id,
                                      materiaimpartida__curso_id=curso_id).distinct()
    data = [{'id': m.id, 'nombre': str(m)} for m in materias]
    return JsonResponse(data, safe=False)

def get_libros_materia(request):
    materia_id = request.GET.get('materia_id')
    libros = LibroTexto.objects.filter(materia_id=materia_id)
    data = [{'id': l.id, 'titulo': l.titulo} for l in libros]
    return JsonResponse(data, safe=False)



def revision_libros(request, profesor_id, momento_id, materia_id, libro_id):
    # Obtener MateriaImpartida concreta
    materia_impartida = MateriaImpartida.objects.filter(
        profesor_id=profesor_id,
        materia_id=materia_id
    ).first()

    if not materia_impartida:
        return render(request, 'error.html', {'mensaje': 'No se ha encontrado la materia impartida.'})

    # Obtener alumnos matriculados
    matriculas = MatriculaMateria.objects.filter(materia_impartida=materia_impartida).select_related('alumno')

    momento = get_object_or_404(MomentoRevisionLibros, pk=momento_id)
    libro = get_object_or_404(LibroTexto, pk=libro_id)
    profesor = get_object_or_404(Profesores, pk=profesor_id)

    contexto = {
        'materia_impartida': materia_impartida,
        'alumnos': [m.alumno for m in matriculas],
        'libro': libro,
        'momento': momento,
        'profesor': profesor,
    }

    return render(request, 'revision_libros.html', contexto)


def get_tabla_revision(request):
    profesor_id = request.GET.get('profesor_id')
    curso_id = request.GET.get('curso_id')
    materia_id = request.GET.get('materia_id')
    libro_id = request.GET.get('libro_id')
    momento_id = request.GET.get('momento_id')

    if not all([profesor_id, curso_id, materia_id, libro_id, momento_id]):
        return JsonResponse({'error': 'Faltan datos'}, status=400)

    # Obtener instancias base
    profesor = Profesores.objects.get(pk=profesor_id)
    materia = Materia.objects.get(pk=materia_id)
    curso = Cursos.objects.get(pk=curso_id)
    libro = LibroTexto.objects.get(pk=libro_id)
    momento = MomentoRevisionLibros.objects.get(pk=momento_id)

    # Buscar la MateriaImpartida concreta
    try:
        materia_impartida = MateriaImpartida.objects.get(
            profesor=profesor,
            materia=materia,
            curso=curso
        )
    except MateriaImpartida.DoesNotExist:
        return JsonResponse({'error': 'No se encontró la asignación de esa materia con ese profesor en ese curso.'}, status=404)

    # Buscar alumnos matriculados en esa materia impartida
    alumnos = MatriculaMateria.objects.filter(
        materia_impartida=materia_impartida
    ).select_related('alumno').order_by('alumno__Nombre')

    estados = momento.estados.all().order_by('orden')

    return render(request, 'includes/tabla_revision_libros.html', {
        'alumnos': [m.alumno for m in alumnos],
        'estados': estados,
        'profesor': profesor,
        'materia': materia,
        'libro': libro,
        'momento': momento,
    })

def guardar_revision_libros(request):

    if request.method == 'POST':
        profesor_id = request.POST.get('profesor')

        if not profesor_id:
            profesor_id = request.user.profesor.id

        curso_id = request.POST.get('curso')
        materia_id = request.POST.get('materia')
        libro_id = request.POST.get('libro')
        momento_id = request.POST.get('momento')

        if not all([profesor_id, curso_id, materia_id, libro_id, momento_id]):
            messages.error(request, "Faltan datos en el formulario.")
            return redirect('revision_libros_inicio')

        profesor = get_object_or_404(Profesores, pk=profesor_id)
        curso = get_object_or_404(Cursos, pk=curso_id)
        materia = get_object_or_404(Materia, pk=materia_id)
        libro = get_object_or_404(LibroTexto, pk=libro_id)
        momento = get_object_or_404(MomentoRevisionLibros, pk=momento_id)

        revision_id = request.POST.get('revision_id')
        if revision_id:
            revision = get_object_or_404(RevisionLibro, id=revision_id)
        else:
            # Crear o recuperar la revisión general
            fecha_hoy = now().date()
            revision, created = RevisionLibro.objects.get_or_create(
                profesor=profesor,
                curso=curso,
                materia=materia,
                libro=libro,
                momento=momento,
                fecha=fecha_hoy,
            )

        # Recoger los datos por alumno
        alumnos_ids = [
            key.split('_')[1] for key in request.POST.keys() if key.startswith('estado_')
        ]

        for alumno_id in alumnos_ids:
            estado_id = request.POST.get(f'estado_{alumno_id}')
            observaciones = request.POST.get(f'observaciones_{alumno_id}', '').strip()

            if not estado_id:
                continue  # Saltar si no se indicó estado

            alumno = get_object_or_404(Alumnos, pk=alumno_id)
            estado = get_object_or_404(EstadoLibro, pk=estado_id)

            # Crear o actualizar la revisión individual
            RevisionLibroAlumno.objects.update_or_create(
                revision=revision,
                alumno=alumno,
                defaults={
                    'estado': estado,
                    'observaciones': observaciones,
                }
            )

        messages.success(request, "Revisión guardada correctamente.")
        return redirect('mis_revisiones')

    return redirect('mis_revisiones')


def resumen_revisiones(request):
    revisiones = RevisionLibro.objects.select_related(
        'profesor', 'materia', 'libro', 'momento', 'curso_academico'
    ).prefetch_related('detalles__alumno')

    resumen = []

    for r in revisiones:
        alumnos_revisados = r.detalles.values_list('alumno_id', flat=True).distinct().count()

        total_matriculados = MatriculaMateria.objects.filter(
            materia_impartida__materia=r.materia,
            materia_impartida__profesor=r.profesor,
            materia_impartida__curso=r.curso,
        ).values('alumno_id').distinct().count()

        resumen.append({
            'id': r.id,
            'profesor': r.profesor,
            'curso': r.curso,
            'materia': r.materia,
            'libro': r.libro,
            'momento': r.momento,
            'curso_academico': r.curso_academico,
            'fecha': r.fecha,
            'revisados': alumnos_revisados,
            'matriculados': total_matriculados,
        })

    resumen.sort(key=lambda r: r['fecha'], reverse=True)

    profesores = sorted(set(str(r['profesor']) for r in resumen))
    cursos = sorted(set(str(r['curso']) for r in resumen))
    materias = sorted(set(str(r['materia']) for r in resumen))
    libros = sorted(set(str(r['libro']) for r in resumen))
    momentos = sorted(set(str(r['momento']) for r in resumen))
    cursosacademicos = sorted(set(str(r['curso_academico']) for r in resumen))

    context = {
        'resumen': resumen,
        'profesores': profesores,
        'cursos': cursos,
        'materias': materias,
        'libros': libros,
        'momentos': momentos,
        'cursosacademicos' : cursosacademicos,
    }

    return render(request, 'resumen_revisiones.html', context)

def detalle_revision(request, revision_id):
    revision = get_object_or_404(
        RevisionLibro.objects.select_related(
            'profesor', 'materia', 'libro', 'momento', 'curso_academico'
        ).prefetch_related('detalles__alumno', 'detalles__estado'),
        pk=revision_id
    )

    return render(request, 'detalle_revision.html', {
        'revisiones': revision.detalles.all(),
        'profesor': revision.profesor,
        'curso': revision.curso,
        'materia': revision.materia,
        'libro': revision.libro,
        'momento': revision.momento,
        'curso_academico': revision.curso_academico,
        'fecha': revision.fecha
    })


def mis_revisiones(request):
    profesor = request.user.profesor
    curso_academico_actual = get_current_academic_year()
    cursos_anteriores = get_previous_academic_years()

    revisiones = RevisionLibro.objects.filter(profesor=profesor).select_related(
        'profesor', 'materia', 'libro', 'momento', 'curso_academico'
    ).prefetch_related('detalles__alumno')

    resumen_actual = []
    resumen_anteriores = {}  # Claves: curso_id

    for r in revisiones:
        alumnos_revisados = r.detalles.values_list('alumno_id', flat=True).distinct().count()

        total_matriculados = MatriculaMateria.objects.filter(
            materia_impartida__materia=r.materia,
            materia_impartida__profesor=r.profesor,
            materia_impartida__curso=r.curso,
        ).values('alumno_id').distinct().count()

        resumen_item = {
            'id': r.id,
            'profesor': r.profesor,
            'curso': r.curso,
            'materia': r.materia,
            'libro': r.libro,
            'momento': r.momento,
            'curso_academico': r.curso_academico,
            'fecha': r.fecha,
            'revisados': alumnos_revisados,
            'matriculados': total_matriculados,
        }

        if r.curso_academico == curso_academico_actual:
            resumen_actual.append(resumen_item)
        elif r.curso_academico.id in [c.id for c in cursos_anteriores]:
            curso_id = r.curso_academico.id
            if curso_id not in resumen_anteriores:
                resumen_anteriores[curso_id] = {
                    'curso': r.curso_academico,
                    'revisiones': []
                }
            resumen_anteriores[curso_id]['revisiones'].append(resumen_item)

    resumen_actual.sort(key=lambda r: r['fecha'], reverse=True)
    for info in resumen_anteriores.values():
        info['revisiones'].sort(key=lambda r: r['fecha'], reverse=True)

    # Construir lista ordenada según cursos_anteriores
    resumen_anteriores_ordenado = []
    for curso in cursos_anteriores:
        curso_id = curso.id
        if curso_id in resumen_anteriores:
            resumen_anteriores_ordenado.append((curso, resumen_anteriores[curso_id]['revisiones']))

    context = {
        'resumen': resumen_actual,
        'resumen_anteriores': resumen_anteriores_ordenado,
    }

    return render(request, 'mis_revisiones.html', context)


def editar_revision_libros(request, revision_id):
    revision = get_object_or_404(RevisionLibro, id=revision_id)
    estados = revision.momento.estados.all().order_by('orden')

    # Obtener la materia impartida desde los datos de la revisión
    try:
        materia_impartida = MateriaImpartida.objects.get(
            profesor=revision.profesor,
            curso=revision.curso,
            materia=revision.materia
        )
    except MateriaImpartida.DoesNotExist:
        materia_impartida = None

    # Obtener todos los alumnos matriculados en esa materia
    alumnos = []
    if materia_impartida:
        matriculas = MatriculaMateria.objects.filter(
            materia_impartida=materia_impartida
        ).select_related('alumno').order_by('alumno__Nombre')
        alumnos = [m.alumno for m in matriculas]

    # Generar lista con revisiones existentes o "vacías"
    alumnos_revisionados = []
    for alumno in alumnos:
        rev_alumno = RevisionLibroAlumno.objects.filter(
            revision=revision, alumno=alumno
        ).first()
        if not rev_alumno:
            # Crear objeto temporal (no guardado en DB)
            rev_alumno = RevisionLibroAlumno(
                revision=revision,
                alumno=alumno,
                estado=None,
                observaciones=''
            )
        alumnos_revisionados.append(rev_alumno)

    return render(request, 'editar_revision.html', {
        'revision': revision,
        'estados': estados,
        'alumnos_revisionados': alumnos_revisionados,
    })
