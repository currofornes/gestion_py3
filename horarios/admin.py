from django.contrib import admin
from .models import ItemHorario

TRAMOS = {
    1: '1ª Hora',
    2: '2ª Hora',
    3: '3ª Hora',
    4: 'RECREO',
    5: '4ª Hora',
    6: '5ª Hora',
    7: '6ª Hora',
}

DIAS = {
    1: 'Lunes',
    2: 'Martes',
    3: 'Miércoles',
    4: 'Jueves',
    5: 'Viernes',
}

@admin.register(ItemHorario)
class ItemHorarioAdmin(admin.ModelAdmin):
    list_display = ['nombre_profesor', 'dia_nombre', 'tramo_nombre', 'unidad', 'materia', 'aula']
    list_filter = ['profesor__Apellidos', 'unidad__Curso', 'materia']
    search_fields = ['profesor__Apellidos', 'profesor__Nombre','materia']
    ordering = ('dia', 'tramo', 'profesor__Apellidos', 'profesor__Nombre')

    icon_name = 'event_note'

    def tramo_nombre(self, obj):
        return TRAMOS[obj.tramo]
    tramo_nombre.short_description = 'Tramo'

    def dia_nombre(self, obj):
        return DIAS[obj.dia]
    dia_nombre.short_description = 'Día'

    def nombre_profesor(self, obj):
        return f'{obj.profesor.Apellidos}, {obj.profesor.Nombre}'
    nombre_profesor.short_description = 'Profesor'

