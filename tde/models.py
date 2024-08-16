from django.db import models

from centro.models import Aulas, Profesores, CursoAcademico


# Create your models here.

class Prioridad(models.Model):
    nombre = models.CharField(max_length=100)
    comentario = models.CharField(max_length=200)
    prioridad = models.IntegerField()

    def __str__(self):
        return self.nombre + " (" + self.comentario + ")"

    class Meta:
        verbose_name="Prioridad"
        verbose_name_plural="Prioridades"


class Elemento(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre




class IncidenciasTic(models.Model):
    fecha = models.DateField()
    profesor = models.ForeignKey(Profesores, on_delete=models.CASCADE)
    aula = models.ForeignKey(Aulas, on_delete=models.CASCADE)
    prioridad = models.ForeignKey(Prioridad, on_delete=models.SET_NULL, null=True)
    comentario = models.TextField()
    elementos = models.ManyToManyField(Elemento)
    resuelta = models.BooleanField(default=False)
    solucion = models.TextField(blank=True, null=True)

    curso_academico = models.ForeignKey(CursoAcademico, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Incidencia en {self.aula} por {self.profesor} con prioridad {self.prioridad}"

    class Meta:
        verbose_name="Incidencia TIC"
        verbose_name_plural="Incidencias TIC"