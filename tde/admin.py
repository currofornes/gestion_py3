from django.contrib import admin
from .models import Prioridad, Elemento, IncidenciasTic

class PrioridadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'comentario', 'prioridad')
    search_fields = ('nombre', 'comentario')
    list_editable = ('prioridad',)

class ElementoAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)
    icon_name = 'devices_other'

class IncidenciasTicAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'profesor', 'aula', 'prioridad', 'resuelta')
    list_filter = ('fecha', 'resuelta', 'prioridad', 'aula')
    search_fields = ('profesor__nombre', 'aula__nombre', 'comentario', 'solucion')
    filter_horizontal = ('elementos',)
    date_hierarchy = 'fecha'
    list_editable = ('resuelta',)
    readonly_fields = ('profesor', 'aula')
    icon_name = 'new_releases'

admin.site.register(Prioridad, PrioridadAdmin)
admin.site.register(Elemento, ElementoAdmin)
admin.site.register(IncidenciasTic, IncidenciasTicAdmin)
