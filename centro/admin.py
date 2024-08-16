from django.contrib import admin
from django import forms
from django.contrib.admin import AdminSite
from django.db import models
from django.urls import path

from centro.models import Cursos, Alumnos, Departamentos, Profesores, Areas, Aulas, Niveles
from django.contrib.admin.widgets import FilteredSelectMultiple

# Register your models here.
class AlumnosAdmin(admin.ModelAdmin):
    # date_hierarchy = 'Fecha_nacimiento'
    actions_selection_counter = False
    list_filter = ['Unidad', 'Localidad']
    list_display = ["Nombre", 'DNI', 'Localidad', 'Telefono1', 'email']

    search_fields = ['Nombre', 'DNI']
    icon_name = 'face'


class ProfesoresAdmin(admin.ModelAdmin):
    # date_hierarchy = 'Fecha_nacimiento'
    actions_selection_counter = False
    list_filter = ['Departamento', 'Baja']
    list_display = ["Nombre", 'Apellidos', 'Email', 'Departamento', 'Baja']

    search_fields = ['Nombre', 'Apellidos']
    icon_name = 'recent_actors'


class DepartamentosAdmin(admin.ModelAdmin):
    actions_selection_counter = False
    list_display = ('Nombre',)
    search_fields = ('Nombre', 'Abr')
    icon_name = 'folder_shared'


class CursosAdmin(admin.ModelAdmin):
    # date_hierarchy = 'Fecha_nacimiento'
    actions_selection_counter = False

    list_display = ["Curso", 'Nivel', 'Tutor', 'Aula']

    search_fields = ['Curso']

    formfield_overrides = {
        models.ManyToManyField: {'widget': FilteredSelectMultiple("Profesores", is_stacked=False)},
    }

    icon_name = 'school'


class AreasAdmin(admin.ModelAdmin):
    actions_selection_counter = False

    list_display = ["Nombre"]

    search_fields = ['Nombre']

    formfield_overrides = {
        models.ManyToManyField: {'widget': FilteredSelectMultiple("Departamentos", is_stacked=False)},
    }

    icon_name = 'widgets'

class AulasAdmin(admin.ModelAdmin):
# date_hierarchy = 'Fecha_nacimiento'
    actions_selection_counter = False
    list_display = ["Aula"]

    search_fields = ['Aula']
    icon_name = 'store'

class NivelesAdmin(admin.ModelAdmin):

    actions_selection_counter = False
    list_display = ["Abr", "Nombre"]

    search_fields = ['Nombre', 'Abr']
    icon_name = 'subject'

# Register your models here.


admin.site.site_header = "Gonzalo Nazareno"
admin.site.index_title = "Gestión del Centro"
admin.site.register(Cursos, CursosAdmin)
admin.site.register(Departamentos)
admin.site.register(Areas, AreasAdmin)
admin.site.register(Alumnos, AlumnosAdmin)
admin.site.register(Profesores, ProfesoresAdmin)
admin.site.register(Aulas, AulasAdmin)
admin.site.register(Niveles, NivelesAdmin)
