from django.urls import re_path, path

from . import views
from .views import cerrar_protocolo

urlpatterns = [
        re_path(r'^misalumnos$', views.misalumnos),
        re_path(r'^alumnos$', views.alumnos),
        re_path(r'^(?P<alum_id>[0-9]+)/protocolo$', views.verprotocolo),
        re_path(r'^protocolo/(?P<proto_id>[0-9]+)/nuevaactuacion$', views.nuevaactuacion),
        re_path(r'^protocolo/(?P<alum_id>[0-9]+)/abrirprotocolo$', views.abrirprotocolo),
        re_path(r'^protocolo/(?P<proto_id>[0-9]+)/ver$', views.verprotocolocerrado),
        path('cerrar_protocolo/', cerrar_protocolo, name='cerrar_protocolo'),

]
