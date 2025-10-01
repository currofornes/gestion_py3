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
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.shortcuts import render, redirect
from django.contrib import messages

# Register your models here.
@admin.register(Alumnos)
class AlumnosAdmin(admin.ModelAdmin):
    # date_hierarchy = 'Fecha_nacimiento'
    actions_selection_counter = False
    list_filter = ['Unidad', 'Localidad']
    list_display = ["Nombre", 'DNI', 'Localidad', 'Telefono1', 'email']

    search_fields = ['Nombre', 'DNI']
    icon_name = 'face'

@admin.register(Profesores)
class ProfesoresAdmin(admin.ModelAdmin):
    # date_hierarchy = 'Fecha_nacimiento'
    actions_selection_counter = False
    list_filter = ['Departamento', 'Baja']
    list_display = ["Nombre", 'Apellidos', 'Email', 'Departamento', 'Baja']

    search_fields = ['Nombre', 'Apellidos']
    icon_name = 'recent_actors'


@admin.register(Departamentos)
class DepartamentosAdmin(admin.ModelAdmin):
    icon_name = 'folder_shared'

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
    list_display = ('curso_academico', 'Alumno', 'Nivel', 'Unidad', 'CentroOrigen', 'Repetidor', 'Edad', 'Sexo')
    list_filter = ('curso_academico', 'Alumno', 'Nivel__Nombre', 'Nivel__Abr', 'Unidad', 'CentroOrigen')
    search_fields = ['Alumno__Nombre', 'Unidad', 'Nivel__Nombre', 'Nivel__Abr', 'CentroOrigen__Codigo', 'CentroOrigen__Nombre']  # Busca por el nombre del alumno
    ordering = ('-curso_academico__año_inicio', 'Nivel__Abr', 'Unidad', 'Alumno__Nombre')


@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    list_display = ['abr', 'nombre', 'nivel', 'horas', 'curso_academico']
    search_fields = ['nombre', 'abr']

@admin.register(MateriaImpartida)
class MateriaImpartidaAdmin(admin.ModelAdmin):
    list_display = ['profesor', 'materia', 'curso', 'curso_academico']
    search_fields = ['materia__nombre', 'profesor__Nombre']

@admin.register(MatriculaMateria)
class MatriculaMateriaAdmin(admin.ModelAdmin):
    list_display = ['alumno', 'materia_impartida', 'curso_academico']
    search_fields = ['alumno__Nombre', 'materia_impartida__materia__nombre']

@admin.register(LibroTexto)
class LibroTextoAdmin(admin.ModelAdmin):
    list_display = ['materia', 'nivel', 'isbn', 'titulo', 'editorial', 'anyo_implantacion', 'importe_estimado', 'es_digital', 'incluir_en_cheque_libro', 'es_otro_material', 'curso_academico']
    search_fields = ['titulo', 'isbn', 'materia__nombre', 'nivel__Nombre']

admin.site.site_header = "Gonzalo Nazareno"
admin.site.index_title = "Gestión del Centro"
