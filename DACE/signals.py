from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from DACE.models import Actividades
from centro.models import CursoAcademico
from centro.utils import get_current_academic_year



@receiver(post_save, sender=Actividades)

def asignar_curso_academico(sender, instance, created, **kwargs):
    if created:
        curso_actual = get_current_academic_year()
        instance.curso_academico = curso_actual
        instance.save()