import datetime
import time
from datetime import date

from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import When, Case
from django.http import JsonResponse
from django.shortcuts import render, get_list_or_404, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from absentismo.forms import ActuacionProtocoloForm
from absentismo.models import ProtocoloAbs
from centro.models import Cursos, Alumnos, Profesores
from centro.views import group_check_prof, is_tutor, group_check_je, group_check_prof_and_tutor_or_je, \
    group_check_prof_and_tutor, group_check_je_or_orientacion, group_check_prof_and_tutor_or_je_or_orientacion


# Create your views here.


@login_required(login_url='/')
@user_passes_test(group_check_prof_and_tutor_or_je_or_orientacion, login_url='/')
def verprotocolo(request, alum_id):
    alum = Alumnos.objects.get(pk=alum_id)
    protocolo = alum.protocolos.filter(abierto=True).last()

    protocolos_cerrados = alum.protocolos.filter(abierto=False)
    protocolos_cerrados = sorted(protocolos_cerrados, key=lambda x: x.fecha_cierre, reverse=False)

    context = {'alum': alum, 'protocolo': protocolo, 'protocolos_cerrados': protocolos_cerrados, 'menu_absentismo': True}
    return render(request, 'protocolos.html', context)


@login_required(login_url='/')
@user_passes_test(group_check_prof_and_tutor, login_url='/')
def misalumnos(request):
    if not hasattr(request.user, 'profesor'):
        return render(request, 'error.html', {'message': 'No tiene un perfil de profesor asociado.'})

    profesor = request.user.profesor

    cursos = Cursos.objects.filter(Tutor_id=profesor.id)
    try:
        primer_id = cursos.order_by('Curso').first().id
    except:
        primer_id = 0

    request.session['Unidad'] = primer_id

    lista_alumnos = Alumnos.objects.filter(Unidad__id=primer_id)
    lista_alumnos = sorted(lista_alumnos, key=lambda d: d.Nombre)


    # Obtener los IDs de los alumnos
    ids = [elem.id for elem in lista_alumnos]

    # Obtener edades y protocolos
    edades = obtener_edades_alumnos(ids)
    protocolos = obtener_protocolos(ids)

    # Combinar alumnos con edades y protocolos
    lista_combinada = list(zip(lista_alumnos, edades, protocolos))


    try:
        context = {'alumnos': lista_combinada, 'curso': cursos.get(id=primer_id), 'profesor': profesor, 'menu_absentismo': True}
    except:
        context = {'alumnos': lista_combinada, 'curso': None, 'profesor': profesor, 'menu_absentismo': True}
    return render(request, 'misalumnosabs.html', context)


def calcular_edad(fecha_nacimiento, fecha_referencia):
    anos = fecha_referencia.year - fecha_nacimiento.year
    if (fecha_referencia.month, fecha_referencia.day) < (fecha_nacimiento.month, fecha_nacimiento.day):
        anos -= 1
    return anos


def obtener_edades_alumnos(ids_alumnos):
    fecha_referencia = date.today()

    # Obtener la lista de alumnos usando los IDs proporcionados
    #alumnos = get_list_or_404(Alumnos, id__in=ids_alumnos)
    # Mantener el orden de los IDs proporcionados
    alumnos = Alumnos.objects.filter(id__in=ids_alumnos).order_by(
        Case(*[When(id=pk, then=pos) for pos, pk in enumerate(ids_alumnos)])
    )

    # Calcular la edad de cada alumno a la fecha de referencia
    edades = [calcular_edad(alumno.Fecha_nacimiento, fecha_referencia) for alumno in alumnos]


    return edades


def obtener_protocolos(ids_alumnos):
    # Obtener alumnos por sus IDs
    #alumnos = get_list_or_404(Alumnos, id__in=ids_alumnos)
    alumnos = Alumnos.objects.filter(id__in=ids_alumnos).order_by(
        Case(*[When(id=pk, then=pos) for pos, pk in enumerate(ids_alumnos)])
    )

    # Crear el listado de resultados
    resultados = []
    for alumno in alumnos:
        protocolo = ProtocoloAbs.objects.filter(alumno=alumno).last()
        if protocolo:
            actuacion = protocolo.actuaciones.last()
            resultados.append({
                'alumno_id': alumno.id,
                'tiene_protocolo': True,
                'protocolo_abierto': protocolo.abierto,
                'fecha_apertura': protocolo.fecha_apertura,
                'fecha_cierre': protocolo.fecha_cierre if protocolo.fecha_cierre else None,
                'ultima_actuacion': actuacion.Tipo if actuacion else None,
                'fecha_ultima': actuacion.Fecha if actuacion else None
            })
        else:
            resultados.append({
                'alumno_id': alumno.id,
                'tiene_protocolo': False,
                'protocolo_abierto': None,
                'fecha_apertura': None,
                'fecha_cierre': None,
                'ultima_actuacion': None,
                'fecha_ultima': None
            })


    return resultados


@login_required(login_url='/')
@user_passes_test(group_check_prof_and_tutor_or_je, login_url='/')
def nuevaactuacion(request, proto_id):
    protocolo = ProtocoloAbs.objects.get(pk=proto_id)
    alum_id = protocolo.alumno.id

    if request.method == 'POST':
        form = ActuacionProtocoloForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/absentismo/' + str(alum_id) + '/protocolo')
        else:
            print(form.errors)
    else:
        form = ActuacionProtocoloForm(
            initial={'Fecha': time.strftime("%d/%m/%Y"), 'Protocolo': protocolo}
        )

    titulo = "Actuaciones Absentismo"

    context = {'form': form, 'titulo': titulo, 'protocolo': protocolo, 'menu_absentismo': True}
    return render(request, 'actuacionprotocolo.html', context)


@csrf_exempt
def cerrar_protocolo(request):
    if request.method == 'POST':
        protocolo_id = request.POST.get('id')
        try:
            protocolo = ProtocoloAbs.objects.get(id=protocolo_id)

            protocolo.abierto = False
            protocolo.fecha_cierre = datetime.date.today().strftime('%Y-%m-%d')
            protocolo.save()

            return JsonResponse({'success': True})
        except ProtocoloAbs.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Protocolo no encontrado'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@login_required(login_url='/')
@user_passes_test(group_check_prof_and_tutor_or_je, login_url='/')
def abrirprotocolo(request, alum_id):
    alumno = get_object_or_404(Alumnos, id=alum_id)  # Obtiene el alumno o lanza 404 si no existe
    tutor = Profesores.objects.get(user=request.user)

    # Verificar si ya existe un ProtocoloAbs abierto para ese alumno
    protocolo_existente = ProtocoloAbs.objects.filter(alumno=alumno, tutor=tutor, abierto=True).first()

    if protocolo_existente:
        # Si ya existe un protocolo abierto, lo utilizamos
        nuevo_protocolo = protocolo_existente
    else:
        nuevo_protocolo = ProtocoloAbs.objects.create(
            alumno=alumno,
            tutor=tutor,
            fecha_apertura=datetime.date.today().strftime('%Y-%m-%d'),  # Asigna la fecha actual
            fecha_cierre=None,
            abierto=True
        )

    form = ActuacionProtocoloForm(
        initial={'Fecha': time.strftime("%d/%m/%Y"), 'Protocolo': nuevo_protocolo}
    )

    titulo = "Actuaciones Absentismo"

    context = {'form': form, 'titulo': titulo, 'protocolo': nuevo_protocolo, 'menu_absentismo': True}
    return render(request, 'actuacionprotocolo.html', context)


@login_required(login_url='/')
@user_passes_test(group_check_prof_and_tutor_or_je_or_orientacion, login_url='/')
def verprotocolocerrado(request, proto_id):
    protocolo = ProtocoloAbs.objects.get(pk=proto_id)
    alumno = protocolo.alumno
    tutor = protocolo.tutor

    context = {'alumno': alumno, 'protocolo': protocolo, 'tutor': tutor, 'menu_absentismo': True}
    return render(request, 'protocolocerrado.html', context)


@login_required(login_url='/')
@user_passes_test(group_check_je_or_orientacion, login_url='/')
def alumnos(request):
    # Obtener todos los protocolos abiertos
    protocolos_abiertos = ProtocoloAbs.objects.filter(abierto=True)

    if not protocolos_abiertos.exists():
        alumnos = []
        context = {'alumnos': alumnos}
    else:
        # Crear una lista de tuplas con (alumno, tutor, edad, protocolo)
        lista_alumnos = []
        for protocolo in protocolos_abiertos:
            alumno = protocolo.alumno
            tutor = protocolo.tutor
            edad = obtener_edades_alumnos([alumno.id])[0]  # Suponiendo que obtener_edades_alumnos devuelve una lista
            protocolo_info = obtener_protocolos([alumno.id])[0]  # Suponiendo que obtener_protocolos devuelve una lista

            # Añadir la tupla a la lista
            lista_alumnos.append((alumno, tutor, edad, protocolo_info))

        # Pasar la lista de tuplas al contexto
        context = {'alumnos': lista_alumnos, 'menu_absentismo': True}

    return render(request, 'alumnosabs.html', context)


@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
def todoalumnado(request):
    if not hasattr(request.user, 'profesor'):
        return render(request, 'error.html', {'message': 'No tiene un perfil de profesor asociado.'})

    profesor = request.user.profesor
    cursos = Cursos.objects.all()

    # Obtener el curso seleccionado desde el formulario (POST)
    curso_id = request.POST.get('curso', None)

    if curso_id:
        lista_alumnos = Alumnos.objects.filter(Unidad_id=curso_id)
        lista_alumnos = sorted(lista_alumnos, key=lambda d: d.Nombre)

        # Obtener los IDs de los alumnos
        ids = [elem.id for elem in lista_alumnos]

        # Obtener edades y protocolos
        edades = obtener_edades_alumnos(ids)
        protocolos = obtener_protocolos(ids)

        # Combinar alumnos con edades y protocolos
        lista_combinada = list(zip(lista_alumnos, edades, protocolos))

        curso_seleccionado = Cursos.objects.get(id=curso_id)
    else:
        # Si no se ha seleccionado ningún curso, inicializamos una lista vacía
        lista_combinada = []
        curso_seleccionado = None

    context = {
        'cursos': cursos,
        'alumnos': lista_combinada,
        'curso_seleccionado': curso_seleccionado,
        'profesor': profesor,
        'menu_absentismo': True
    }

    return render(request, 'todoalumnado.html', context)