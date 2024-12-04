from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from centro.models import CursoAcademico
from centro.utils import get_current_academic_year
from convivencia.models import Amonestaciones, Sanciones, PropuestasSancion


@receiver(post_save, sender=Amonestaciones)
@receiver(post_save, sender=Sanciones)
def asignar_curso_academico(sender, instance, created, **kwargs):
    if created:
        curso_actual = get_current_academic_year()
        instance.curso_academico = curso_actual
        instance.save()

@receiver(post_save, sender=Sanciones)
def cerrar_registro_alumnado_sancionable(sender, instance, **kwargs):
    alumno = instance.IdAlumno
    curso = instance.curso_academico
    if not alumno or not curso:
        return  # No se puede procesar si falta el alumno o el curso académico

    # Buscar registro existente en AlumnadoSancionable
    try:
        propuesta = PropuestasSancion.objects.get(
            alumno=alumno,
            curso_academico=curso,
            salida__isnull=True
        )
        propuesta.salida = instance.Fecha
        propuesta.motivo_salida = "Sanción"
        propuesta.save()
    except PropuestasSancion.DoesNotExist:
        # No hay registro activo, no se hace nada
        pass

@receiver(post_save, sender=Amonestaciones)
def actualizar_alumnado_sancionable(sender, instance, **kwargs):
    alumno = instance.IdAlumno
    curso = instance.curso_academico
    if not alumno or not curso:
        return  # No se puede procesar si falta el alumno o el curso académico

    # Buscar registro existente en AlumnadoSancionable
    propuestas = PropuestasSancion.objects.filter(
        Q(curso_academico=curso) & Q(salida__isnull=True) & Q(alumno=alumno)).all()
    if len(propuestas) > 0:
        propuesta = propuestas[0]
        propuesta.ultima_amonestacion = instance
        propuesta.ignorar = False
        propuesta.save()
    else:
        if alumno.sancionable:
            propuesta = PropuestasSancion(
                curso_academico=curso,
                alumno=alumno,
                entrada=instance.Fecha,
                ultima_amonestacion=instance
            )

            propuesta.save()