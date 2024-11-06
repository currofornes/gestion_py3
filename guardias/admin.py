from django.contrib import admin

from guardias.models import ItemGuardia, TiempoGuardia


# Register your models here.
class ItemGuardiaAdmin(admin.ModelAdmin):
    icon_name = 'schedule'

class TiempoGuardiaAdmin(admin.ModelAdmin):
    icon_name = 'timer'

admin.site.register(ItemGuardia, ItemGuardiaAdmin)
admin.site.register(TiempoGuardia, TiempoGuardiaAdmin)
