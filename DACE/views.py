from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from .models import Actividades
from centro.models import Profesores
from .forms import ActividadesForm

@login_required
def crear_actividad(request):
    if request.method == 'POST':
        form = ActividadesForm(request.POST)
        if form.is_valid():
            actividad = form.save(commit=False)
            actividad.estado = 'Pendiente'
            actividad.save()
            form.save_m2m()  # para guardar relaciones ManyToMany
            return redirect('lista_actividades')
    else:
        profe = Profesores.objects.filter(user=request.user).first()
        form = ActividadesForm({'Responsable': profe})
    return render(request, 'crear_actividad.html', {'form': form, 'menu_DACE': True})

# @login_required
# def aprobar_actividad(request, actividad_id):
#     actividad = get_object_or_404(Actividad, id=actividad_id)
#     if request.method == 'POST':
#         form = AprobacionForm(request.POST)
#         if form.is_valid():
#             aprobacion = form.save(commit=False)
#             aprobacion.actividad = actividad
#             aprobacion.aprobado_por = request.user
#             aprobacion.save()
#             actividad.estado = 'Aprobada'
#             actividad.save()
#             return redirect('lista_actividades')
#     else:
#         form = AprobacionForm()
#     return render(request, 'gestion/aprobar_actividad.html', {'form': form, 'actividad': actividad})

# @login_required
# def calendario_actividades(request):
#     actividades = Actividad.objects.filter(estado='Aprobada')
#     return render(request, 'gestion/calendario_actividades.html', {'actividades': actividades})