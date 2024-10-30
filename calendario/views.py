from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from datetime import date, timedelta
from convivencia.models import Amonestaciones, Sanciones
from centro.models import Alumnos
from centro.views import group_check_je

# ToDo: Añadir texto a loes eventos de calendario.

# Create your views here.
@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
def faltas(request, alum_id):
    return render(request, 'calendario.html')

@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
def faltas_json(request, alum_id):
    # Cargar faltas a día completo de la BBDD
    # Hard coded en pruebas
    faltasNJ_dia_completo = [
        date.fromisoformat('2024-09-23'),
        date.fromisoformat('2024-09-24'),
        date.fromisoformat('2024-09-25'),
        date.fromisoformat('2024-09-26'),
        date.fromisoformat('2024-09-27'),
        date.fromisoformat('2024-09-30'),
        date.fromisoformat('2024-10-01'),
        date.fromisoformat('2024-10-02'),
        date.fromisoformat('2024-10-03'),
        date.fromisoformat('2024-10-08'),
        date.fromisoformat('2024-10-09'),
        date.fromisoformat('2024-10-10'),
        date.fromisoformat('2024-10-11'),
        date.fromisoformat('2024-10-15'),
        date.fromisoformat('2024-10-16'),
        date.fromisoformat('2024-10-17'),
        date.fromisoformat('2024-10-18'),
        date.fromisoformat('2024-10-22'),
    ]
    # Cargar faltas a tramos de la BBDD
    # Hard coded en pruebas
    faltasNJ_tramos = [
        date.fromisoformat('2024-09-16'),
        date.fromisoformat( '2024-09-17'),
        date.fromisoformat('2024-09-18'),
        date.fromisoformat('2024-09-19'),
        date.fromisoformat('2024-09-20'),
        date.fromisoformat('2024-10-04'),
        date.fromisoformat('2024-10-07'),
        date.fromisoformat('2024-10-14'),
    ]

    return JsonResponse(
        {
            'NJ_diacompleto': faltasNJ_dia_completo,
            'NJ_tramos': faltasNJ_tramos
        }, safe=False)

@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
def amonestaciones(request, alum_id):
    alumno = Alumnos.objects.get(id=alum_id)
    context = {
        'alumno': alumno
    }
    return render(request, "amonestaciones.html", context)

@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
def amonestaciones_json(request, alum_id):
    amonestaciones = Amonestaciones.objects.filter(IdAlumno_id=alum_id)
    sanciones = Sanciones.objects.filter(IdAlumno_id=alum_id)

    leves = []
    graves = []
    lsanciones = []

    for amonestacion in amonestaciones:
        amonestacion_data = {
            'start': amonestacion.Fecha.strftime("%Y-%m-%d"),
            'className': 'bg-warning' if amonestacion.Tipo.TipoFalta == "L" else 'bg-secondary',
            'modalInfo': [
                {'label': 'Tipo de amonestación.', 'text': amonestacion.Tipo.TipoAmonestacion},
                {'label': 'Descripción:', 'text':amonestacion.Comentario}
            ]
        }
        if amonestacion.Tipo.TipoFalta == "L":
            leves.append(amonestacion_data)
        elif amonestacion.Tipo.TipoFalta == "G":
            graves.append(amonestacion_data)

    for sancion in sanciones:
        inicio = sancion.Fecha.strftime("%Y-%m-%d")
        final = (sancion.Fecha_fin + timedelta(days=1)).strftime("%Y-%m-%d")
        lsanciones.append({
            'start': inicio,
            'end': final,
            'className': 'bg-danger',
            'modalInfo': [
                {'label': 'Sanción:', 'text': sancion.Sancion},
                {'label': 'Comentario:', 'text': sancion.Comentario}
            ]
        })

    return JsonResponse({
        'leves': leves,
        'graves': graves,
        'sanciones': lsanciones
    }, safe=False)