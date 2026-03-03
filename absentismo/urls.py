"""
╔════════════════════════════════════════════════════════════════════════════╗
║                          GESTION@ - GESTIÓN DE CENTROS EDUCATIVOS          ║
║                                                                            ║
║ Copyright © 2023-2026 Francisco Fornés Rumbao, Raúl Reina Molina           ║
║                          Proyecto base por José Domingo Muñoz Rodríguez    ║
║                                                                            ║
║ Todos los derechos reservados. Prohibida la reproducción, distribución,    ║
║ modificación o comercialización sin consentimiento expreso de los autores. ║
║                                                                            ║
║ Este archivo es parte de la aplicación Gestion@.                           ║
║                                                                            ║
║ Para consultas sobre licencias o permisos:                                 ║
║ Email: fforrum559@g.educaand.es                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
"""


from django.urls import re_path, path

from . import views
from .views import cerrar_protocolo

urlpatterns = [
    # path('misalumnos', views.misalumnos),
    path(
        'alumnos',
        views.alumnos
    ),
    path(
        '<int:alum_id>/protocolo',
        views.verprotocolo,
        name='detalle_protocolo'
    ),
    path(
        'protocolo/<int:proto_id>/nuevaactuacion',
        views.nuevaactuacion
    ),
    path(
        'protocolo/<int:alum_id>/abrirprotocolo',
        views.abrirprotocolo
    ),
    path(
        'protocolo/<int:proto_id>/ver',
        views.verprotocolocerrado
    ),
    path(
        'protocolo/<int:proto_id>/cargarfaltas',
        views.cargarfaltas
    ),
    path(
        'cerrar_protocolo/',
        cerrar_protocolo,
        name='cerrar_protocolo'
    ),
    path(
        'todoalumnado',
        views.todoalumnado
    ),
    path(
        'protocolo/<int:protocolo_id>/calendario_asistencia',
        views.calendario_asistencia,
        name='calendario_asistencia'
    ),
    path(
        'protocolo/<int:protocolo_id>/calendario_asistencia/pdf/',
        views.descargar_pdf_calendario,
        name='descargar_pdf_calendario'
    ),
    path(
        'protocolo/<int:proto_id>/ver_resumen_faltas',
        views.resumen_faltas_periodos,
        name='resumen_faltas_periodos'
    ),
    path(
        'protocolo/<int:protocolo_id>/informe-fm/',
        views.editar_informe_fm,
        name='editar_informe_fm'
    ),
    path(
        'protocolo/<int:protocolo_id>/informe-fm/pdf/',
        views.descargar_pdf_fm,
        name='descargar_pdf_fm'

    ),
    path(
        'protocolo/<int:protocolo_id>/informe-ssc/',
        views.editar_informe_ssc,
        name='editar_informe_ssc'
    ),
    path(
        'protocolo/<int:protocolo_id>/informe-ssc/pdf/',
        views.descargar_pdf_ssc,
        name='descargar_pdf_ssc'
    ),
    # ── Adjuntos FM ───────────────────────────────────────────────────────────
    path(
        'protocolo/<int:protocolo_id>/informe-fiscalia/adjunto/subir/',
        views.subir_adjunto_fm,
        name='subir_adjunto_fm'
    ),
    path(
        'adjunto-fm/<int:adjunto_id>/eliminar/',
        views.eliminar_adjunto_fm,
        name='eliminar_adjunto_fm'
    ),
    path(
        'adjunto-fm/<int:adjunto_id>/descripcion/',
        views.actualizar_descripcion_adjunto_fm,
        name='actualizar_descripcion_adjunto_fm'
    ),

    # ── Adjuntos SSC ──────────────────────────────────────────────────────────
    path(
        'protocolo/<int:protocolo_id>/informe-ssc/adjunto/subir/',
        views.subir_adjunto_ssc,
        name='subir_adjunto_ssc'
    ),
    path(
        'adjunto-ssc/<int:adjunto_id>/eliminar/',
        views.eliminar_adjunto_ssc,
        name='eliminar_adjunto_ssc'
    ),
    path(
        'adjunto-ssc/<int:adjunto_id>/descripcion/',
        views.actualizar_descripcion_adjunto_ssc,
        name='actualizar_descripcion_adjunto_ssc'
    ),
]
