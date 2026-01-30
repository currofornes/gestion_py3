from django.contrib import admin
from .models import CampanaTransito, InformeDepartamento, AsignacionMateriaDepartamento
from centro.models import Materia, CursoAcademico
from centro.utils import get_current_academic_year

class AsignacionMateriaInline(admin.TabularInline):
    model = AsignacionMateriaDepartamento
    extra = 1
    # Recuerda: si usas autocomplete aquí, asegúrate de tener search_fields en MateriaAdmin (centro/admin.py)
    # autocomplete_fields = ['departamento']

    verbose_name = "Departamento Responsable"
    verbose_name_plural = "Asignación de Materias a Departamentos"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Filtra las materias basándose en las materias definidas en la Configuración
        de la campaña actual.
        """
        if db_field.name == "materia":
            # Intentamos obtener el ID de la campaña desde la URL
            try:
                # Captura el ID de la campaña que estamos editando en el admin
                parent_id = request.resolver_match.kwargs.get('object_id')

                if parent_id:
                    campana = CampanaTransito.objects.get(id=parent_id)
                    # LÓGICA CORREGIDA:
                    # Accedemos a la configuración y de ahí a sus materias M2M
                    if campana:
                        kwargs["queryset"] = campana.materias_implicadas.all().order_by('abr')

            except CampanaTransito.DoesNotExist:
                # Si estamos creando la campaña y aún no existe, el queryset será el default (todas)
                # o vacío, hasta que se guarde por primera vez.
                pass

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class InformeInline(admin.TabularInline):
    """
    Permite ver (y añadir) los informes dentro de la pantalla de la Campaña.
    Útil para un vistazo rápido de cuántos informes se han entregado.
    """
    model = InformeDepartamento
    extra = 0
    # Campos que se muestran en el resumen (ajusta según tus necesidades)
    fields = ('materia', 'centro_origen')
    readonly_fields = ('materia', 'centro_origen')
    show_change_link = True  # Permite ir al detalle del informe
    can_delete = False



@admin.register(CampanaTransito)
class CampanaTransitoAdmin(admin.ModelAdmin):
    # 1. Definimos el orden exacto de los campos según tu solicitud
    fields = (
        'descripcion',
        'curso_academico',
        'cerrada',
        'niveles',  # 3. Lista doble de niveles
        'materias_implicadas',  # 4. Lista doble de materias (filtrada)
        'centros_origen'  # 5. Lista doble de centros (lo que llamabas departamentos/centros)
    )
    inlines = [AsignacionMateriaInline, InformeInline]
    list_display = ('descripcion', 'curso_academico', 'cerrada',  'get_niveles', 'get_materias_count', 'get_centros_count')
    list_editable = ('cerrada',)
    list_filter = ('curso_academico', 'cerrada')
    search_fields = ('descripcion',)

    # Activamos el widget de doble panel (selector horizontal) para los tres campos
    filter_horizontal = ('niveles', 'materias_implicadas', 'centros_origen')

    # actions = ['marcar_como_cerradas', 'marcar_como_abiertas']
    #
    # @admin.action(description='Cerrar campañas seleccionadas')
    # def marcar_como_cerradas(self, request, queryset):
    #     updated = queryset.update(cerrada=True)
    #     self.message_user(request, f"{updated} campañas han sido cerradas.")
    #
    # @admin.action(description='Reabrir campañas seleccionadas')
    # def marcar_como_abiertas(self, request, queryset):
    #     updated = queryset.update(cerrada=False)
    #     self.message_user(request, f"{updated} campañas han sido reabiertas.")

    def get_niveles(self, obj):
        return ", ".join([n.Abr for n in obj.niveles.all()])

    get_niveles.short_description = "Niveles"

    def get_materias_count(self, obj):
        return obj.materias_implicadas.count()

    get_materias_count.short_description = "Nº Materias"

    def get_centros_count(self, obj):
        return obj.centros_origen.count()

    get_centros_count.short_description = "Nº Centros"

    # LÓGICA DE FILTRADO DEPENDIENTE
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "materias_implicadas":
            # Obtenemos el ID de la campaña que se está editando (si existe)
            object_id = request.resolver_match.kwargs.get('object_id')

            if object_id:
                # MODO EDICIÓN: Ya tenemos curso y niveles guardados
                campana = CampanaTransito.objects.get(id=object_id)
                curso = campana.curso_academico
                niveles = campana.niveles.all()

                if curso and niveles.exists():
                    # FILTRO MAGISTRAL:
                    # Materias que pertenecen al Curso Académico seleccionado
                    # Y ADEMÁS pertenecen a alguno de los Niveles seleccionados
                    kwargs["queryset"] = Materia.objects.filter(
                        curso_academico=curso,
                        nivel__in=niveles
                    ).distinct().order_by('nombre')

                    kwargs["help_text"] = f"Mostrando materias del curso {curso} y niveles seleccionados."
                else:
                    kwargs["queryset"] = Materia.objects.none()
                    kwargs["help_text"] = "No se han detectado niveles seleccionados en la base de datos."

            else:
                # MODO CREACIÓN: El usuario aún no ha guardado nada
                kwargs["queryset"] = Materia.objects.none()
                kwargs["help_text"] = (
                    "⚠️ <strong>ACCIÓN REQUERIDA:</strong> Selecciona primero la Descripción, "
                    "el Curso Académico y los Niveles. Luego pulsa <strong>'Guardar y continuar editando'</strong> "
                    "para poder seleccionar las materias."
                )

        return super().formfield_for_manytomany(db_field, request, **kwargs)


@admin.register(InformeDepartamento)
class InformeDepartamentoAdmin(admin.ModelAdmin):
    list_display = ('materia', 'centro_origen', 'campana')
    list_filter = (
        'campana__curso_academico',  # Filtrar por año
        'materia',  # Filtrar por departamento
        'centro_origen',  # Filtrar por colegio
    )
    search_fields = (
        'materia__nombre',  # Asumo que Materia tiene campo 'nombre'
        'centro_origen__nombre',  # Asumo que Centros tiene campo 'nombre'
    )
    # Agrupamos los campos para que el formulario de admin sea ordenado
    fieldsets = (
        ('Contexto', {
            'fields': ('campana', 'materia', 'centro_origen')
        }),
        ('Análisis Cualitativo', {
            'fields': ('cuestiones_generales', 'fortalezas', 'debilidades'),
            'classes': ('wide',),  # Ocupa todo el ancho
        }),
    )