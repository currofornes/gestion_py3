from django.urls import re_path, path

from . import views
from .views import busqueda

urlpatterns = [
        re_path(r'^alumnos$', views.alumnos),
        re_path(r'^alumnos/(?P<curso>[0-9]+)$', views.alumnos_curso),
        re_path(r'^profesores/change/Baja/(?P<codigo>[0-9]+)/(?P<operacion>[a-z]+)$', views.profesores_change),
        re_path(r'^profesores$', views.profesores),
        re_path(r'^cursos$', views.cursos),
        re_path(r'^misalumnos$', views.misalumnos),
        path('busqueda/', busqueda, name='busqueda'),

]
