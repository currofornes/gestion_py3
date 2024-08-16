from django.urls import re_path, path

from . import views
from .views import eliminar_incidencia, actualizar_incidencia

urlpatterns = [

    re_path(r'^incidenciaticprofe$', views.incidenciaticprofe, name='incidenciaticprofe'),
    re_path(r'^misincidenciastic$', views.misincidenciastic, name='misincidenciastic'),
    re_path(r'^incidenciastic$', views.incidenciastic, name='incidenciastic'),
    path('eliminar_incidencia/', eliminar_incidencia, name='eliminar_incidencia'),
    path('actualizar_incidencia/', actualizar_incidencia, name='actualizar_incidencia'),


]
