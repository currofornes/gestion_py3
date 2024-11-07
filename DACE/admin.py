from django.contrib import admin

from DACE.models import Actividades, Aprobaciones


class ActividadesAdmin(admin.ModelAdmin):
    list_display = ['Titulo', 'FechaInicio', 'Duracion', 'MedidaDuracion' ,'Estado']


class AprobacionesAdmin(admin.ModelAdmin):
    list_display = ['Actividad', 'AprobadoPor', 'Fecha']


admin.site.register(Actividades, ActividadesAdmin)
admin.site.register(Aprobaciones, AprobacionesAdmin)
