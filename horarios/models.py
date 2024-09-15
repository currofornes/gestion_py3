from django.db import models

# Create your models here.

from django.db import models
from centro.models import Profesores, Cursos, Aulas  # Asegúrate de que las relaciones están correctas

class ItemHorario(models.Model):
    TRAMOS = [(i, f'Tramo {i}') for i in range(1, 8)]
    DIAS = [(i, f'Día {i}') for i in range(1, 6)]

    tramo = models.IntegerField(choices=TRAMOS)
    dia = models.IntegerField(choices=DIAS)
    profesor = models.ForeignKey(Profesores, on_delete=models.CASCADE)
    unidad = models.ForeignKey(Cursos, on_delete=models.CASCADE)
    aula = models.ForeignKey(Aulas, on_delete=models.CASCADE)
    materia = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.profesor} - Día {self.dia} Tramo {self.tramo}"

    class Meta:
        verbose_name = "Item de Horario"
        verbose_name_plural = "Items de Horario"
        unique_together = ('tramo', 'dia', 'profesor', 'unidad', 'aula')