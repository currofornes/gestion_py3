from django.db import models

from centro.models import Profesores, CursoAcademico


# Create your models here.
class TiposReserva(models.Model):
    TipoReserva = models.CharField(max_length=60)

    def __str__(self):
        return self.TipoReserva

    class Meta:
        verbose_name = "Tipo Reserva"
        verbose_name_plural = "Tipos de Reservas"


class Reservables(models.Model):
    Nombre = models.CharField(max_length=255)
    Descripcion = models.CharField(max_length=255)
    TiposReserva = models.ForeignKey(TiposReserva, related_name='Tipo_de', blank=True, null=True, on_delete=models.SET_NULL)


    def __str__(self):
        return self.Nombre


    class Meta:
        verbose_name = "Reservable"
        verbose_name_plural = "Reservables"


class Reservas(models.Model):
    hora = (
        ('1', 'Primera (1ª)'),
        ('2', 'Segunda (2ª)'),
        ('3', 'Tercera (3ª)'),
        ('4', 'Recreo (REC)'),
        ('5', 'Cuarta (4ª)'),
        ('6', 'Quinta (5ª)'),
        ('7', 'Sexta (6ª)'),

    )


    Profesor = models.ForeignKey(Profesores, null=True, on_delete=models.SET_NULL)
    Fecha = models.DateField()
    Hora = models.CharField(max_length=1, choices=hora, default='1')
    Reservable = models.ForeignKey(Reservables, null=True, on_delete=models.SET_NULL, related_name='reservable')

    curso_academico = models.ForeignKey(CursoAcademico, on_delete=models.SET_NULL, null=True, blank=True)


    def __str__(self):
        return self.Reservable.Nombre


    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
