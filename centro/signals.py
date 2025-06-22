from django.db.models.signals import pre_save
from django.dispatch import receiver

from centro.models import RevisionLibroAlumno, CursoAcademico, RevisionLibro
from centro.utils import get_current_academic_year

@receiver(pre_save, sender=RevisionLibro)
def asignar_curso_academico(sender, instance, **kwargs):
    if not instance.curso_academico:
        try:
            curso_actual = get_current_academic_year()
            instance.curso_academico = curso_actual
        except CursoAcademico.DoesNotExist:
            instance.curso_academico = None  # O lanza una excepción si lo prefieres

