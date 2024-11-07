from django.urls import path
from . import views

urlpatterns = [
    path('crear_actividad/', views.crear_actividad, name='crear_actividad'),
    # path('aprobar_actividad/<int:actividad_id>/', views.aprobar_actividad, name='aprobar_actividad'),
    # path('calendario_actividades/', views.calendario_actividades, name='calendario_actividades'),
]
