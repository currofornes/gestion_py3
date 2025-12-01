"""
╔════════════════════════════════════════════════════════════════════════════╗
║                          GESTION@ - GESTIÓN DE CENTROS EDUCATIVOS         ║
║                                                                            ║
║ Copyright © 2023-2025 Francisco Fornés Rumbao, Raúl Reina Molina          ║
║                          Proyecto base por José Domingo Muñoz Rodríguez    ║
║                                                                            ║
║ Todos los derechos reservados. Prohibida la reproducción, distribución,   ║
║ modificación o comercialización sin consentimiento expreso de los autores. ║
║                                                                            ║
║ Este archivo es parte de la aplicación Gestion@.                          ║
║                                                                            ║
║ Para consultas sobre licencias o permisos:                                ║
║ Email: fforrum559@g.educaand.es                                           ║
╚════════════════════════════════════════════════════════════════════════════╝
"""


from django.urls import include, re_path, path
from . import views

urlpatterns = [
    path('ver_analisis/', views.analisis, name='analisis'),
    path('ver_analisis/recalcular_indicadores/', views.recalcular_indicadores),
    path('analisis_pdf/', views.GenerarPDFView.as_view(), name='analisis_pdf'),
    path('analisis_por_centros_1_ESO/', views.analisis_por_centros_1_ESO),
    path('analisis_1ESO_pdf/', views.GenerarPDF1ESOView.as_view(), name='analisis_1ESO_pdf'),
]