from django.urls import re_path, path

from . import views
from .views import busqueda

urlpatterns = [
        path('alumnos', views.alumnos),
        path('alumnos/<int:curso>', views.alumnos_curso),
        path('profesores/change/Baja/<int:codigo>/<str:operacion>', views.profesores_change),
        path('profesores', views.profesores),
        path('cursos', views.cursos),
        path('misalumnos', views.misalumnos),
        path('busqueda/', busqueda, name='busqueda'),

]
