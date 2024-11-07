from django.db import models
from centro.models import Cursos, Alumnos, Profesores

class Actividades(models.Model):
    ESTADO_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('Aprobada', 'Aprobada'),
    ]

    DURACION_CHOICES = [
        ('Dias', 'Días'),
        ('Horas', 'Horas'),
    ]

    Titulo = models.CharField(max_length=255)
    Responsable = models.ForeignKey(Profesores, on_delete=models.CASCADE, related_name='actividades_organizadas')
    FechaInicio = models.DateField()
    Duracion = models.PositiveSmallIntegerField()  # Duración en días u horas
    MedidaDuracion = models.CharField(max_length=10, choices=DURACION_CHOICES, default='Horas')
    UnidadesAfectadas = models.ManyToManyField(Cursos)
    Alumnado = models.ManyToManyField(Alumnos)
    Profesorado = models.ManyToManyField(Profesores, related_name="actividades_participadas")
    CosteAlumnado = models.DecimalField(max_digits=8, decimal_places=2)
    DietasProfesorado = models.DecimalField(max_digits=8, decimal_places=2)
    Estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='Pendiente')

    def __str__(self):
        return self.titulo


class Aprobaciones(models.Model):
    APROBACION_CHOICES = [
        ('Consejo Escolar', 'Consejo Escolar'),
        ('Comisión Permanente', 'Comision Permanente'),
    ]
    Actividad = models.ForeignKey(Actividades, on_delete=models.CASCADE, related_name='aprobaciones')
    AprobadoPor = models.CharField(max_length=50, choices=APROBACION_CHOICES)
    Fecha = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"Aprobación de {self.actividad.titulo}"

