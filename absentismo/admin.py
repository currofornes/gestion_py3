from django.contrib import admin
from .models import TiposActuaciones, ProtocoloAbs, Actuaciones
from centro.models import Alumnos, Profesores

class ActuacionesInline(admin.TabularInline):
    model = Actuaciones
    extra = 1

class ProtocoloAbsAdmin(admin.ModelAdmin):
    list_display = ('alumno', 'tutor', 'fecha_apertura', 'fecha_cierre', 'abierto')
    list_filter = ('abierto', 'fecha_apertura', 'tutor')
    search_fields = ('alumno__Nombre', 'tutor__Nombre')
    inlines = [ActuacionesInline]
    icon_name = 'contact_mail'

class ActuacionesAdmin(admin.ModelAdmin):
    list_display = ('Protocolo', 'Fecha', 'Tipo', 'Notificada', 'Medio', 'Telefono')
    list_filter = ('Tipo', 'Notificada', 'Medio')
    search_fields = ('Protocolo__alumno__Nombre', 'Comentario', 'Telefono')
    date_hierarchy = 'Fecha'
    icon_name = 'contact_phone'

class TiposActuacionesAdmin(admin.ModelAdmin):
    list_display = ('TipoActuacion',)
    search_fields = ('TipoActuacion',)

admin.site.register(TiposActuaciones, TiposActuacionesAdmin)
admin.site.register(ProtocoloAbs, ProtocoloAbsAdmin)
admin.site.register(Actuaciones, ActuacionesAdmin)
