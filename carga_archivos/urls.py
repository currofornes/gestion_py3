from django.urls import include, re_path, path
from . import views

urlpatterns = [
    path('calificaciones/', views.calificaciones, name='calificaciones'),
    path('calificaciones/procesar/', views.calificaciones_procesar_datos, name='calificaciones_procesar_datos'),
    path('RegAlum/', views.regalum, name='RegAlum'),
    path('RegAlum/procesar/', views.RegAlum_procesar_datos, name='RegAlum_procesar_datos'),
    path('admision/', views.admision, name='admision'),
    path('admision/procesar/', views.admision_procesar_datos, name='admision_procesar'),
]