from django.urls import re_path, path

from . import views
from .views import EditarHorarioProfesorView, UpdateHorarioView, DeleteHorarioView, CrearItemHorarioView

urlpatterns = [

    re_path(r'^horarioprofe$', views.horario_profesor_view, name='horario_profesor_view'),
    re_path(r'^horariogrupo$', views.horario_curso_view, name='horario_curso_view'),

    re_path(r'^mihorario$', views.mihorario, name='mihorario'),

    re_path(r'^aulaslibres$', views.aulas_libres, name='aulas_libres'),

    path('profesor/<int:profesor_id>/editar/', EditarHorarioProfesorView.as_view(), name='editar_horario_profesor'),
    path('horario/<int:pk>/editar_item/', UpdateHorarioView.as_view(), name='editar_item_horario'),

    path('item/<int:pk>/eliminar/', DeleteHorarioView.as_view(), name='eliminar_item_horario'),

    path('horario/<int:profesor_id>/crear_item/', CrearItemHorarioView.as_view(), name='crear_item_horario'),

    path('copiar_horario/', views.copiar_horario, name='copiar_horario'),




]
