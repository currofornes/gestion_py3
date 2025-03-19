from django.db.models import Q
from django.db.models.signals import post_save, post_delete
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
        propuesta.amonestaciones.add(instance)
        propuesta.ignorar = False
        if instance.gravedad == "Leve":
            propuesta.leves += 1
            propuesta.peso += 1
        elif instance.gravedad == "Grave":
            propuesta.graves += 1
            propuesta.peso += 2
        propuesta.save()
    else:
        leves = alumno.leves
        graves = alumno.graves
        peso = leves + 2 * graves
        if peso >= 4:
            propuesta = PropuestasSancion(
                curso_academico=curso,
                alumno=alumno,
                entrada=instance.Fecha,
                leves=leves,
                graves=graves,
                peso=peso
            )
            propuesta.save()
            for amonestacion in alumno.amonestaciones_vigentes:
                propuesta.amonestaciones.add(amonestacion)
                propuesta.save()
            for amonestacion in propuesta.amonestaciones.all():
                if not amonestacion.vigente:
                    propuesta.amonestaciones.delete(amonestacion)
                    propuesta.save()
