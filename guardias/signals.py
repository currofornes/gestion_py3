from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction

from .models import ItemGuardia, TiempoGuardia, Profesores
from centro.utils import get_current_academic_year

# --------- Asignar curso académico al crear ItemGuardia y TiempoGuardia ---------
@receiver(post_save, sender=ItemGuardia)
@receiver(post_save, sender=TiempoGuardia)
def asignar_curso_academico(sender, instance, created, **kwargs):
    if created and not hasattr(instance, '_curso_asignado'):
        if instance.curso_academico is None:
            curso_actual = get_current_academic_year()
            instance.curso_academico = curso_actual
            instance._curso_asignado = True
            instance.save()

