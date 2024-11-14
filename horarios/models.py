from django.db import models

# Create your models here.

from django.db import models
from centro.models import Profesores, Cursos, Aulas  # Asegúrate de que las relaciones están correctas

class ItemHorario(models.Model):
    TRAMOS = [
        (1, '1ª Hora'),
        (2, '2ª Hora'),
        (3, '3ª Hora'),
        (4, 'RECREO'),
        (5, '4ª Hora'),
        (6, '5ª Hora'),
        (7, '6ª Hora'),
    ]

    DIAS = [
        (1, 'Lunes'),
        (2, 'Martes'),
        (3, 'Miércoles'),
        (4, 'Jueves'),
        (5, 'Viernes'),
    ]

    tramo = models.IntegerField(choices=TRAMOS)
    dia = models.IntegerField(choices=DIAS)
    profesor = models.ForeignKey(Profesores, on_delete=models.CASCADE)
    unidad = models.ForeignKey(Cursos, on_delete=models.CASCADE)
    aula = models.ForeignKey(Aulas, on_delete=models.CASCADE)
    materia = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.profesor} - {self.materia} - {self.unidad} - {self.aula} - {self.get_dia_display()} {self.get_tramo_display()}"

    class Meta:
        verbose_name = "Item de Horario"
        verbose_name_plural = "Items de Horario"
        unique_together = ('tramo', 'dia', 'profesor', 'unidad', 'aula', 'materia')