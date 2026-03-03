from django.contrib import admin
from django.utils import timezone
from django.db.models.functions import Lower

from .models import TiposActuaciones, ProtocoloAbs, Actuaciones, FaltasProtocolo
from centro.models import Alumnos, Profesores
from datetime import date


# Filtro personalizado para detectar alumnos >= 16 años
class EdadCumplidaFilter(admin.SimpleListFilter):
    title = 'Edad actual'
    parameter_name = 'es_mayor_16'

    def lookups(self, request, model_admin):
        return (
            ('si', 'Mayor o igual a 16 años'),
            ('no', 'Menor de 16 años'),
        )

    def queryset(self, request, queryset):
        # Calculamos la fecha límite (hoy hace 16 años)
        fecha_limite = date.today().replace(year=date.today().year - 16)

        if self.value() == 'si':
            return queryset.filter(alumno__Fecha_nacimiento__lte=fecha_limite)
        if self.value() == 'no':
            return queryset.filter(alumno__Fecha_nacimiento__gt=fecha_limite)


class ActuacionesInline(admin.TabularInline):
    model = Actuaciones
    extra = 1
    classes = ['collapse']

class FaltasProtocoloInline(admin.TabularInline):
    model = FaltasProtocolo
    extra = 0  # No añade filas vacías por defecto si ya hay datos
    fields = ('Fecha', 'DiaCompletoNoJustificada', 'TramosNoJustificados',
              'DiaCompletoJustificada', 'TramosJustificados')
    classes = ['collapse'] # Opcional: permite contraer la sección para no alargar mucho la página
    verbose_name = "Falta de asistencia"
    verbose_name_plural = "Historial de Faltas asociadas al protocolo"


@admin.register(ProtocoloAbs)
class ProtocoloAbsAdmin(admin.ModelAdmin):
    list_display = ('alumno', 'get_unidad', 'tutor', 'fecha_apertura',
                    'fecha_cierre', 'abierto', 'get_edad')

    # Actualizamos list_filter para incluir la Unidad del alumno
    # Django detectará automáticamente si hay valores nulos y ofrecerá "Desconocido" o "None"
    list_filter = (
        'abierto',
        EdadCumplidaFilter,
        'alumno__Unidad',
        # Filtro por unidad con opción de nulos
        'fecha_apertura',
        'tutor'
    )
    search_fields = ('alumno__Nombre', 'alumno__Unidad', 'tutor__Nombre')
    inlines = [ActuacionesInline, FaltasProtocoloInline]
    icon_name = 'contact_mail'
    actions = ['cerrar_protocolos_masivo']

    ordering = ('-alumno__Fecha_nacimiento',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "tutor":
            # 1. Filtramos: Activos, Apellidos válidos y que sean tutores (Tutor_de)
            queryset = Profesores.objects.filter(
                Baja=False,
                Apellidos__isnull=False,
                Tutor_de__isnull=False
            ).exclude(
                Apellidos='-'
            ).exclude(
                Apellidos=''
            ).order_by('Apellidos', 'Nombre').distinct()

            kwargs["queryset"] = queryset

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @admin.display(description='Unidad', ordering='alumno__Unidad')
    def get_unidad(self, obj):
        return obj.alumno.Unidad

    @admin.display(description='Edad actual')
    def get_edad(self, obj):
        if obj.alumno.Fecha_nacimiento:
            today = date.today()
            born = obj.alumno.Fecha_nacimiento
            return today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        return "-"

    @admin.action(description="Cerrar protocolos seleccionados (Baja masiva)")
    def cerrar_protocolos_masivo(self, request, queryset):
        filas_actualizadas = queryset.update(
            abierto=False,
            fecha_cierre=timezone.now().date()
        )
        self.message_user(request, f"Se han cerrado correctamente {filas_actualizadas} protocolos.")


@admin.register(Actuaciones)
class ActuacionesAdmin(admin.ModelAdmin):
    list_display = ('Protocolo', 'Fecha', 'Tipo', 'Notificada', 'Medio',
                    'Telefono')
    list_filter = ('Tipo', 'Notificada', 'Medio', 'Fecha')
    search_fields = ('Protocolo__alumno__Nombre', 'Comentario', 'Telefono')
    date_hierarchy = 'Fecha'
    autocomplete_fields = ['Protocolo']
    icon_name = 'contact_phone'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('Protocolo__alumno',
                                                            'Tipo')


@admin.register(TiposActuaciones)
class TiposActuacionesAdmin(admin.ModelAdmin):
    list_display = ('TipoActuacion',)
    search_fields = ('TipoActuacion',)


@admin.register(FaltasProtocolo)
class FaltasProtocoloAdmin(admin.ModelAdmin):
    list_display = ('Protocolo', 'Fecha')
    autocomplete_fields = ['Protocolo']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('Protocolo__alumno')