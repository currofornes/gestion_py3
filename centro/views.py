import os
import time

import unicodedata
from django.db.models import Q
from django.http import HttpResponseForbidden, FileResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from centro.models import Alumnos, Cursos, Departamentos, Profesores
from centro.utils import get_current_academic_year
from convivencia.models import Amonestaciones, Sanciones
from centro.forms import UnidadForm, DepartamentosForm, UnidadProfeForm, UnidadesProfeForm
from datetime import datetime

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
    lista = zip(lista_alumnos, ContarFaltas(ids), EstaSancionado(ids))
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


def ContarFaltas(lista_id):
    curso_academico_actual = get_current_academic_year()

    contar = []
    for alum in lista_id:
        alumno_id = list(alum.values())[0]

        # Filtrar por el curso académico actual
        am = str(len(Amonestaciones.objects.filter(IdAlumno_id=alumno_id, curso_academico=curso_academico_actual)))
        sa = str(len(Sanciones.objects.filter(IdAlumno_id=alumno_id, curso_academico=curso_academico_actual)))

        contar.append(am + "/" + sa)
    return contar


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
    lista = zip(lista_alumnos, ContarFaltas(ids), EstaSancionado(ids))
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


