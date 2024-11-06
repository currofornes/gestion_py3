from django.contrib import admin
from .models import ItemHorario

class ItemHorarioAdmin(admin.ModelAdmin):
    icon_name = 'event_note'



admin.site.register(ItemHorario, ItemHorarioAdmin)



