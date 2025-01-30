from django.contrib import admin
from django.utils.html import format_html
from convivencia.models import Amonestaciones, Sanciones, TiposAmonestaciones, PropuestasSancion


# Register your models here.

@admin.register(Amonestaciones)
class AmonestacionesAdmin(admin.ModelAdmin):
    #date_hierarchy = 'Fecha_nacimiento'
    actions_selection_counter=False
    list_filter = ['Fecha','Profesor']
    list_display = ["Fecha","IdAlumno","unidad","Comentario"]
    icon_name = 'sentiment_very_dissatisfied'

    def unidad(self, obj):
        return obj.IdAlumno.Unidad

    unidad.admin_order_field = "IdAlumno__Unidad"
     
     
    search_fields = ['Comentario']

@admin.register(Sanciones)
class SancionesAdmin(admin.ModelAdmin):
    #date_hierarchy = 'Fecha_nacimiento'
    actions_selection_counter=False
    list_filter = ['Fecha']
    list_display = ["Fecha","Fecha_fin","IdAlumno","unidad","Sancion"]

    def unidad(self, obj):
        return obj.IdAlumno.Unidad

    unidad.admin_order_field = 'IdAlumno__Unidad'
     
    search_fields = ['Comentario']
    icon_name = 'exit_to_app'


@admin.register(PropuestasSancion)
class PropuestasSancionAdmin(admin.ModelAdmin):
    list_display = ('alumno_nombre', 'curso_acad', 'entrada', 'salida', 'leves', 'graves', 'peso', 'ignorar', 'acciones')
    list_filter = ('curso_academico', 'ignorar', 'entrada', 'salida')
    search_fields = ('alumno__Nombre', 'curso_academico__nombre')
    ordering = (('curso_academico', '-peso'))

    def alumno_nombre(self, obj):
        return f"{obj.alumno.Nombre} ({obj.alumno.Unidad})"
    alumno_nombre.short_description = 'Alumno'

    def curso_acad(self, obj):
        return obj.curso_academico.nombre
    curso_acad.short_description = 'Curso Académico'

    def acciones(self, obj):
        """Muestra un enlace para ignorar la propuesta en el admin."""
        if not obj.ignorar:
            return format_html(
                '<a href="/convivencia/ignorar/{}/" class="button">Ignorar</a>', obj.id
            )
        return "Ignorada"

    acciones.allow_tags = True
    acciones.short_description = "Acciones"

    fieldsets = (
        ("Información del alumno", {
            "fields": ("alumno", "curso_academico")
        }),
        ("Detalles de la sanción", {
            "fields": ("entrada", "salida", "motivo_salida", "amonestaciones")
        }),
        ("Cálculo de la sanción", {
            "fields": ("leves", "graves", "peso", "ignorar")
        }),
    )
