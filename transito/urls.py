from django.urls import path
from . import views

app_name = 'transito'

urlpatterns = [
    # Vista principal (Pantalla de informe)
    path('informe/', views.gestion_informe_transito, name='gestion_informe'),

    # API AJAX (Backend para el script de JS)
    path('api/check-informe/', views.api_check_informe, name='api_check_informe'),
    path('descargar-informe/', views.DescargarInformePDFView.as_view(), name='descargar_informe'),
    path('rendimiento-departamentos/', views.RendimientoDepartamentosPDFView.as_view(), name='rendimiento_departamentos'),
    path('introducir-historico/', views.IntroducirInformeHistoricoView.as_view(), name='introducir_historico'),
]