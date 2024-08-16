from django.contrib import admin
from .models import TiposReserva, Reservables, Reservas

class TiposReservaAdmin(admin.ModelAdmin):
    list_display = ('TipoReserva',)
    search_fields = ('TipoReserva',)

class ReservablesAdmin(admin.ModelAdmin):
    list_display = ('Nombre', 'Descripcion', 'TiposReserva')
    list_filter = ('TiposReserva',)
    search_fields = ('Nombre', 'Descripcion', 'TiposReserva__TipoReserva')
    icon_name = 'devices'

class ReservasAdmin(admin.ModelAdmin):
    list_display = ('Profesor', 'Fecha', 'Hora', 'Reservable')
    list_filter = ('Fecha', 'Hora', 'Reservable__TiposReserva')
    search_fields = ('Profesor__Nombre', 'Reservable__Nombre', 'Reservable__TiposReserva__TipoReserva')
    date_hierarchy = 'Fecha'
    icon_name = 'assignment'

admin.site.register(TiposReserva, TiposReservaAdmin)
admin.site.register(Reservables, ReservablesAdmin)
admin.site.register(Reservas, ReservasAdmin)