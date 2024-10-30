from django.urls import re_path, path

from . import views
from .views import cerrar_protocolo

urlpatterns = [
        path('misalumnos', views.misalumnos),
        path('alumnos', views.alumnos),
        path('<int:alum_id>/protocolo', views.verprotocolo),
        path('protocolo/<int:proto_id>/nuevaactuacion$', views.nuevaactuacion),
        path('protocolo/<int_alum_id>/abrirprotocolo$', views.abrirprotocolo),
        path('protocolo/<int:proto_id>/ver$', views.verprotocolocerrado),
        path('protocolo/<int:proto_id>/cargarfaltas', views.cargarfaltas),
        path('cerrar_protocolo/', cerrar_protocolo, name='cerrar_protocolo'),
        path('todoalumnado', views.todoalumnado),

]
