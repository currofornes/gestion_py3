from django.contrib import admin
from django import forms
from django.contrib.admin import AdminSite
from django.db import models
from django.urls import path

from centro.forms import AsignarProfesoresDepartamentoForm
from centro.models import (
    Cursos, Alumnos, Departamentos, Profesores, Areas, Aulas, Niveles, CursoAcademico, InfoAlumnos, Centros, Materia,
    MateriaImpartida, MatriculaMateria, LibroTexto
)
from centro.utils import get_current_academic_year
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.shortcuts import render, redirect
from django.contrib import messages

# Register your models here.
class MatriculaMateriaInline(admin.TabularInline):
    model = MatriculaMateria
    extra = 1
    autocomplete_fields = ['materia_impartida'] # Búsqueda rápida de materia/profe
    fields = ['materia_impartida', 'curso_academico']

class MateriaImpartidaInline(admin.TabularInline):
    model = MateriaImpartida
    extra = 0
    classes = ['collapse']  # Esto permite colapsar el inline completo en algunas versiones de Django
    autocomplete_fields = ['materia', 'curso']
    verbose_name = "Materia que imparte"
    verbose_name_plural = "Materias que imparte"

class InfoAlumnosInline(admin.TabularInline):
    model = InfoAlumnos
    extra = 0  # No añade filas vacías por defecto
    classes = ['collapse']  # Esto permite colapsar el inline completo en algunas versiones de Django
    fields = ('curso_academico', 'Nivel', 'Unidad', 'Repetidor', 'Edad', 'Sexo', 'CentroOrigen')
    # Si quieres que aparezca de forma más compacta, usa admin.TabularInline


@admin.register(Alumnos)
class AlumnosAdmin(admin.ModelAdmin):
    actions_selection_counter = False
    icon_name = 'face'

    # Listado principal
    list_display = ["Nombre", 'Unidad', 'DNI', 'Centro_EP', 'Telefono1', 'email']
    list_filter = ['Unidad', 'Localidad', 'Centro_EP']
    search_fields = ['Nombre', 'DNI']

    # Organización del formulario en "secciones/pestañas"
    fieldsets = (
        # 1. Información principal (Siempre visible)
        (None, {
            'fields': ('Nombre', 'Unidad')
        }),
        # 2. Identificación (Oculta por defecto)
        ('Información de Identificación', {
            'classes': ('collapse',),
            'fields': ('NIE', 'DNI', 'Fecha_nacimiento')
        }),
        # 3. Datos de contacto y residencia (Oculta por defecto)
        ('Dirección y Ubicación', {
            'classes': ('collapse',),
            'fields': ('Direccion', 'CodPostal', 'Localidad', 'Provincia')
        }),
        # 4. Centros de procedencia (Oculta por defecto)
        ('Historial Escolar (Centros)', {
            'classes': ('collapse',),
            'fields': ('Centro_EP', 'Centro_ESO')
        }),
        # Otros campos que no mencionaste pero están en el modelo (opcional)
        ('Datos del Tutor y Observaciones', {
            'classes': ('collapse',),
            'fields': (('Nomtutor', 'Ap1tutor', 'Ap2tutor'), ('Telefono1', 'Telefono2'), 'email', 'Obs',
                       ('PDC', 'NEAE'))
        }),
    )

    # 5 y 6. Inlines
    # Nota: Los inlines en Django estándar aparecen siempre al final.
    # No se pueden "colapsar" de la misma forma que los fieldsets sin JS personalizado,
    # pero aparecerán en el orden indicado abajo.
    inlines = [MatriculaMateriaInline, InfoAlumnosInline]


@admin.register(Profesores)
class ProfesoresAdmin(admin.ModelAdmin):
    # date_hierarchy = 'Fecha_nacimiento'
    actions_selection_counter = False
    list_filter = ['Departamento', 'Baja']
    list_display = ["Nombre", 'Apellidos', 'Email', 'Departamento', 'Baja']
    inlines = [MateriaImpartidaInline]  # Ver carga horaria en la ficha del profe
    search_fields = ['Nombre', 'Apellidos']
    icon_name = 'recent_actors'


@admin.register(Departamentos)
class DepartamentosAdmin(admin.ModelAdmin):
    icon_name = 'folder_shared'
    search_fields = ['Nombre', 'Abr']

    change_list_template = "admin/departamentos_changelist.html"  # Usar una plantilla personalizada

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('asignar-profesores/', self.admin_site.admin_view(self.asignar_profesores_view), name="asignar_profesores"),
        ]
        return custom_urls + urls

    def asignar_profesores_view(self, request):
        if request.method == 'POST':
            form = AsignarProfesoresDepartamentoForm(request.POST)
            if form.is_valid():
                departamento = form.cleaned_data['departamento']
                profesores = form.cleaned_data['profesores']
                for profesor in profesores:
                    profesor.Departamento = departamento
                    profesor.save()
                messages.success(request, "Profesores asignados correctamente al departamento.")
                return redirect('admin:index')
        else:
            form = AsignarProfesoresDepartamentoForm()

        context = {
            'form': form,
            'title': "Asignar Profesores a un Departamento"
        }
        return render(request, 'admin/asignar_profesores.html', context)


'''
class DepartamentosAdmin(admin.ModelAdmin):
    actions_selection_counter = False
    list_display = ('Nombre',)
    search_fields = ('Nombre', 'Abr')
    icon_name = 'folder_shared'
'''

@admin.register(Cursos)
class CursosAdmin(admin.ModelAdmin):
    # date_hierarchy = 'Fecha_nacimiento'
    actions_selection_counter = False

    list_display = ["Curso", 'Nivel', 'Tutor', 'Aula', 'Activo']

    search_fields = ['Curso']

    formfield_overrides = {
        models.ManyToManyField: {'widget': FilteredSelectMultiple("Profesores", is_stacked=False)},
    }

    icon_name = 'school'

    # Filtro para que puedas filtrar por activo/inactivo en el admin
    list_filter = ['Activo']

    def get_queryset(self, request):
        """Override el queryset para el admin, para que se muestren todos los cursos sin filtrar por defecto"""
        return Cursos.all_objects.all()  # Usamos el manager sin filtro


@admin.register(Areas)
class AreasAdmin(admin.ModelAdmin):
    actions_selection_counter = False

    list_display = ["Nombre"]

    search_fields = ['Nombre']

    formfield_overrides = {
        models.ManyToManyField: {'widget': FilteredSelectMultiple("Departamentos", is_stacked=False)},
    }

    icon_name = 'widgets'

@admin.register(Aulas)
class AulasAdmin(admin.ModelAdmin):
# date_hierarchy = 'Fecha_nacimiento'
    actions_selection_counter = False
    list_display = ["Aula"]

    search_fields = ['Aula']
    icon_name = 'store'

@admin.register(Niveles)
class NivelesAdmin(admin.ModelAdmin):

    actions_selection_counter = False
    list_display = ["Abr", "Nombre", 'NombresAntiguos']

    search_fields = ['Nombre', 'Abr']
    icon_name = 'subject'


@admin.register(CursoAcademico)
class CursoAcademicoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'año_inicio', 'año_fin')
    list_filter = ('año_inicio', 'año_fin')
    search_fields = ('nombre', 'año_inicio', 'año_fin')
    ordering = ('-año_inicio',)

@admin.register(Centros)
class CentrosAdmin(admin.ModelAdmin):
    list_display = ('Codigo', 'Nombre')
    list_filter = ('Codigo', 'Nombre')
    search_fields = ('Nombre', 'Codigo')
    ordering = ('Nombre', 'Codigo')


@admin.register(InfoAlumnos)
class InfoAlumnosAdmin(admin.ModelAdmin):
    # Añadimos 'unidad_anterior' al list_display
    list_display = ('curso_academico', 'Alumno', 'get_unidad_anterior', 'Unidad', 'Nivel', 'CentroOrigen', 'Repetidor')
    list_filter = ('curso_academico', 'Alumno', 'Nivel__Nombre', 'Nivel__Abr', 'Unidad', 'CentroOrigen')
    search_fields = ['Alumno__Nombre', 'Unidad', 'Nivel__Nombre', 'Nivel__Abr', 'CentroOrigen__Codigo',
                     'CentroOrigen__Nombre']
    ordering = ('-curso_academico__año_inicio', 'Nivel__Abr', 'Unidad', 'Alumno__Nombre')

    # Añadimos la acción a la lista
    actions = ['asignar_gonzalo_nazareno']

    @admin.action(description="Asignar IES Gonzalo Nazareno como Centro de Origen")
    def asignar_gonzalo_nazareno(self, request, queryset):
        try:
            # Buscamos el centro por el código proporcionado
            centro_gn = Centros.objects.get(Codigo='41011038')

            # Actualizamos el campo CentroOrigen de todos los registros seleccionados en el queryset
            filas_actualizadas = queryset.update(CentroOrigen=centro_gn)

            self.message_user(
                request,
                f"Se ha asignado correctamente el IES Gonzalo Nazareno a {filas_actualizadas} registros.",
                messages.SUCCESS
            )
        except Centros.DoesNotExist:
            self.message_user(
                request,
                "Error: No se ha encontrado ningún centro con el código 41011038 en la base de datos.",
                messages.ERROR
            )

    @admin.display(description='Unidad Año Anterior')
    def get_unidad_anterior(self, obj):
        # 1. Obtenemos el curso académico anterior usando la lógica de tu modelo
        try:
            curso_previo = obj.curso_academico - 1  # Resta un año al inicio
        except (TypeError, NotImplementedError):
            return "-"

        if curso_previo:
            # 2. Buscamos el registro de InfoAlumnos para ese alumno en el año anterior
            registro_anterior = InfoAlumnos.objects.filter(
                Alumno=obj.Alumno,
                curso_academico=curso_previo
            ).first()

            return registro_anterior.Unidad if registro_anterior else "N/A"

        return "-"


@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    # 1. Configuración del Listado (Interfaz principal)
    list_display = ('nombre', 'abr', 'nivel', 'horas', 'curso_academico', 'get_num_profesores')
    list_filter = ('curso_academico', 'nivel', 'horas')
    search_fields = ('nombre', 'abr')
    list_editable = ('abr', 'horas')  # Permite correcciones rápidas sin entrar en la ficha
    ordering = ('-curso_academico__año_inicio', 'nivel', 'nombre')
    list_per_page = 50

    # 2. Organización del Formulario de Edición
    fieldsets = (
        ('Información Básica', {
            'fields': (('nombre', 'abr'), ('nivel', 'horas'))
        }),
        ('Configuración de Sistema', {
            'fields': ('curso_academico',),
            'classes': ('collapse',)  # Por defecto oculto para no estorbar
        }),
    )

    # 3. Relaciones y Componentes
    inlines = [MateriaImpartidaInline]

    # 4. Acciones Personalizadas
    actions = ['clonar_materias_al_curso_actual']

    @admin.display(description='Profesores')
    def get_num_profesores(self, obj):
        """Muestra cuántos profesores imparten esta materia actualmente"""
        return obj.materiaimpartida_set.count()

    @admin.action(description="Clonar materias seleccionadas al curso académico actual")
    def clonar_materias_al_curso_actual(self, request, queryset):
        """
        Acción para copiar materias de años anteriores al curso actual con un solo clic.
        """
        curso_actual = get_current_academic_year()
        contador = 0

        for materia in queryset:
            # Evitamos duplicar si ya existe en el curso actual
            if materia.curso_academico == curso_actual:
                continue

            # Clonamos el objeto cambiando solo el curso académico
            materia.pk = None
            materia.curso_academico = curso_actual
            materia.save()
            contador += 1

        if contador > 0:
            self.message_user(request, f"Se han clonado {contador} materias al curso {curso_actual}.", messages.SUCCESS)
        else:
            self.message_user(request, "No se clonaron materias (o ya pertenecían al curso actual).", messages.WARNING)



@admin.register(MateriaImpartida)
class MateriaImpartidaAdmin(admin.ModelAdmin):
    list_display = ['get_materia_nombre', 'profesor', 'curso', 'curso_academico']
    list_filter = ['curso_academico', 'curso', 'materia__nivel']
    search_fields = ['materia__nombre', 'profesor__Nombre', 'profesor__Apellidos']
    autocomplete_fields = ['profesor', 'materia', 'curso']

    @admin.display(description='Materia', ordering='materia__nombre')
    def get_materia_nombre(self, obj):
        return obj.materia.nombre

@admin.register(MatriculaMateria)
class MatriculaMateriaAdmin(admin.ModelAdmin):
    list_display = ['alumno', 'get_unidad', 'get_materia', 'get_profesor', 'curso_academico']
    list_filter = ['curso_academico', 'materia_impartida__curso', 'materia_impartida__materia__nivel']
    search_fields = ['alumno__Nombre', 'materia_impartida__materia__nombre', 'materia_impartida__profesor__Nombre']
    autocomplete_fields = ['alumno', 'materia_impartida']

    @admin.display(description='Unidad', ordering='materia_impartida__curso')
    def get_unidad(self, obj):
        return obj.materia_impartida.curso

    @admin.display(description='Materia')
    def get_materia(self, obj):
        return obj.materia_impartida.materia

    @admin.display(description='Profesor')
    def get_profesor(self, obj):
        return obj.materia_impartida.profesor

@admin.register(LibroTexto)
class LibroTextoAdmin(admin.ModelAdmin):
    list_display = ['materia', 'nivel', 'isbn', 'titulo', 'editorial', 'anyo_implantacion', 'importe_estimado', 'es_digital', 'incluir_en_cheque_libro', 'es_otro_material', 'curso_academico']
    search_fields = ['titulo', 'isbn', 'materia__nombre', 'nivel__Nombre']

admin.site.site_header = "Gonzalo Nazareno"
admin.site.index_title = "Gestión del Centro"
