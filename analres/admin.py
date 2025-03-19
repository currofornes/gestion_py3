from django.contrib import admin
from analres.models import Calificaciones, IndicadoresAlumnado


@admin.register(Calificaciones)
class CalificacionesAdmin(admin.ModelAdmin):
    list_display = ['curso_academico', 'Nivel', 'alumno_nombre', 'Materia', 'Convocatoria', 'Calificacion']
    list_filter = ['curso_academico', 'Convocatoria']
    search_fields = ['Alumno__Nombre']
    ordering = ['curso_academico', 'Nivel', 'Convocatoria', 'Alumno__Nombre', 'Materia']

    class Meta:
        verbose_name = 'Calificaciones'
        verbose_name_plural = 'Calificaciones'

    def alumno_nombre(self, obj):
        return f"{obj.Alumno.Nombre}"
    alumno_nombre.short_description = 'Alumno'

@admin.register(IndicadoresAlumnado)
class IndicadoresAlumnadoAdmin(admin.ModelAdmin):
    convocatorias = {
        'EVI': 'Evaluación inicial',
        '1EV': '1ª Evaluación',
        '2EV': '2ª Evaluacion',
        '3EV': '3ª Evaluacion',
        'FFP': 'Final FP',
        'Ord': 'Ordinaria',
        'Ext': 'Extraordinaria'
    }

    list_display = ['curso_acad', 'alumno_nombre', 'nivel', 'conv', 'Modalidad',
                    'EstimacionPromocion', 'EficaciaTransito', 'EvaluacionPositivaTodo', 'EficaciaRepeticion',
                    'IdoneidadCursoEdad', 'AbandonoEscolar']
    search_fields = ['Alumno__Nombre']
    list_filter = ['curso_academico', 'Convocatoria']
    ordering = ['curso_academico', 'Alumno__Nombre', 'Convocatoria']

    def curso_acad(self, obj):
        return obj.curso_academico.nombre
    curso_acad.short_description = 'Curso Académico'

    def nivel(self, obj):
        return obj.Alumno.info_adicional.filter(curso_academico=obj.curso_academico).first().Nivel
    nivel.short_description = 'Nivel'

    def alumno_nombre(self, obj):
        return f"{obj.Alumno.Nombre}"
    alumno_nombre.short_description = 'Alumno'

    def conv(self, obj):
        return self.convocatorias[obj.Convocatoria]
    conv.short_description = 'Convocatoria'