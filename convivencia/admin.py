from django.contrib import admin
from convivencia.models import Amonestaciones,Sanciones,TiposAmonestaciones
# Register your models here.


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

admin.site.register(TiposAmonestaciones)
admin.site.register(Amonestaciones,AmonestacionesAdmin)
admin.site.register(Sanciones,SancionesAdmin)

