from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from centro.utils import get_current_academic_year
from .models import ItemHorario


@receiver(post_save, sender=ItemHorario)
def asignar_curso_academico(sender, instance, created, **kwargs):
    if created and not hasattr(instance, '_curso_asignado'):
        curso_actual = get_current_academic_year()
        if instance.curso_academico != curso_actual:
            instance.curso_academico = curso_actual
            instance._curso_asignado = True
            instance.save()


'''
def sincronizar_horario(sender, instance, created, **kwargs):
    prof = instance.profesor

    # Evitar bucles infinitos con un flag (opcional)
    if hasattr(instance, '_sincronizando'):
        return

    # Si es sustituto, sincroniza el horario al titular
    if prof.SustitutoDe:
        titular = prof.SustitutoDe
        data = {
            'tramo': instance.tramo,
            'dia': instance.dia,
            'profesor': titular,
            'unidad': instance.unidad,
            'aula': instance.aula,
            'materia': instance.materia,
            'curso_academico': instance.curso_academico,
        }
        horario, created = ItemHorario.objects.update_or_create(
            tramo=data['tramo'],
            dia=data['dia'],
            profesor=data['profesor'],
            unidad=data['unidad'],
            aula=data['aula'],
            materia=data['materia'],
            curso_academico=data['curso_academico'],
            defaults=data
        )
        horario._sincronizando = True  # Flag para evitar reentrada
        horario.save()

    # Si es titular, sincroniza a todos sus sustitutos
    else:
        sustitutos = prof.sustitutos.all()
        for sustituto in sustitutos:
            data = {
                'tramo': instance.tramo,
                'dia': instance.dia,
                'profesor': sustituto,
                'unidad': instance.unidad,
                'aula': instance.aula,
                'materia': instance.materia,
                'curso_academico': instance.curso_academico,
            }
            horario, created = ItemHorario.objects.update_or_create(
                tramo=data['tramo'],
                dia=data['dia'],
                profesor=data['profesor'],
                unidad=data['unidad'],
                aula=data['aula'],
                materia=data['materia'],
                curso_academico=data['curso_academico'],
                defaults=data
            )
            horario._sincronizando = True
            horario.save()


@receiver(post_delete, sender=ItemHorario)
def eliminar_horario_sincronizado(sender, instance, **kwargs):
    prof = instance.profesor

    if prof.SustitutoDe:
        ItemHorario.objects.filter(
            tramo=instance.tramo,
            dia=instance.dia,
            profesor=prof.SustitutoDe,
            unidad=instance.unidad,
            aula=instance.aula,
            materia=instance.materia,
            curso_academico=instance.curso_academico,
        ).delete()
    else:
        for sustituto in prof.sustitutos.all():
            ItemHorario.objects.filter(
                tramo=instance.tramo,
                dia=instance.dia,
                profesor=sustituto,
                unidad=instance.unidad,
                aula=instance.aula,
                materia=instance.materia,
                curso_academico=instance.curso_academico,
            ).delete()

'''