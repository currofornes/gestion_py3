from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import ItemGuardia, TiempoGuardia, Profesores
from centro.utils import get_current_academic_year

# --------- Asignar curso académico al crear ItemGuardia y TiempoGuardia ---------
@receiver(post_save, sender=ItemGuardia)
@receiver(post_save, sender=TiempoGuardia)
def asignar_curso_academico(sender, instance, created, **kwargs):
    if created and not hasattr(instance, '_curso_asignado'):
        curso_actual = get_current_academic_year()
        if instance.curso_academico != curso_actual:
            instance.curso_academico = curso_actual
            instance._curso_asignado = True
            instance.save()

# --------- Sincronización de ItemGuardia ---------
@receiver(post_save, sender=ItemGuardia)
def sincronizar_item_guardia(sender, instance, created, **kwargs):
    prof = instance.ProfesorAusente
    if prof is None:
        return
    if hasattr(instance, '_sincronizando'):
        return

    if prof.SustitutoDe:
        titular = prof.SustitutoDe
        guardia, created = ItemGuardia.objects.update_or_create(
            Unidad=instance.Unidad,
            ProfesorAusente=titular,
            Aula=instance.Aula,
            Tarea=instance.Tarea,
            Materia=instance.Materia,
            Fecha=instance.Fecha,
            Tramo=instance.Tramo,
            ProfesorNotifica=instance.ProfesorNotifica,
            ProfesorConfirma=instance.ProfesorConfirma,
            curso_academico=instance.curso_academico,
            defaults={
                'Unidad': instance.Unidad,
                'Aula': instance.Aula,
                'Tarea': instance.Tarea,
                'Materia': instance.Materia,
                'Fecha': instance.Fecha,
                'Tramo': instance.Tramo,
                'ProfesorNotifica': instance.ProfesorNotifica,
                'ProfesorConfirma': instance.ProfesorConfirma,
                'curso_academico': instance.curso_academico,
            }
        )
        guardia._sincronizando = True
        guardia.save()
        guardia.ProfesoresGuardia.set(instance.ProfesoresGuardia.all())

    else:
        for sustituto in prof.sustitutos.all():
            guardia, created = ItemGuardia.objects.update_or_create(
                Unidad=instance.Unidad,
                ProfesorAusente=sustituto,
                Aula=instance.Aula,
                Tarea=instance.Tarea,
                Materia=instance.Materia,
                Fecha=instance.Fecha,
                Tramo=instance.Tramo,
                ProfesorNotifica=instance.ProfesorNotifica,
                ProfesorConfirma=instance.ProfesorConfirma,
                curso_academico=instance.curso_academico,
                defaults={
                    'Unidad': instance.Unidad,
                    'Aula': instance.Aula,
                    'Tarea': instance.Tarea,
                    'Materia': instance.Materia,
                    'Fecha': instance.Fecha,
                    'Tramo': instance.Tramo,
                    'ProfesorNotifica': instance.ProfesorNotifica,
                    'ProfesorConfirma': instance.ProfesorConfirma,
                    'curso_academico': instance.curso_academico,
                }
            )
            guardia._sincronizando = True
            guardia.save()
            guardia.ProfesoresGuardia.set(instance.ProfesoresGuardia.all())

@receiver(post_delete, sender=ItemGuardia)
def eliminar_item_guardia_sincronizado(sender, instance, **kwargs):
    prof = instance.ProfesorAusente
    if prof is None:
        return
    if prof.SustitutoDe:
        ItemGuardia.objects.filter(
            Unidad=instance.Unidad,
            ProfesorAusente=prof.SustitutoDe,
            Aula=instance.Aula,
            Tarea=instance.Tarea,
            Materia=instance.Materia,
            Fecha=instance.Fecha,
            Tramo=instance.Tramo,
            ProfesorNotifica=instance.ProfesorNotifica,
            ProfesorConfirma=instance.ProfesorConfirma,
            curso_academico=instance.curso_academico,
        ).delete()
    else:
        for sustituto in prof.sustitutos.all():
            ItemGuardia.objects.filter(
                Unidad=instance.Unidad,
                ProfesorAusente=sustituto,
                Aula=instance.Aula,
                Tarea=instance.Tarea,
                Materia=instance.Materia,
                Fecha=instance.Fecha,
                Tramo=instance.Tramo,
                ProfesorNotifica=instance.ProfesorNotifica,
                ProfesorConfirma=instance.ProfesorConfirma,
                curso_academico=instance.curso_academico,
            ).delete()

# --------- Sincronización de TiempoGuardia ---------
@receiver(post_save, sender=TiempoGuardia)
def sincronizar_tiempo_guardia(sender, instance, created, **kwargs):
    prof = instance.profesor
    if prof is None:
        return
    if hasattr(instance, '_sincronizando'):
        return

    if prof.SustitutoDe:
        titular = prof.SustitutoDe
        tiempo, created = TiempoGuardia.objects.update_or_create(
            profesor=titular,
            dia_semana=instance.dia_semana,
            tramo=instance.tramo,
            item_guardia=instance.item_guardia,  # Asegura que igualas item_guardia si es necesario
            defaults={
                'tiempo_asignado': instance.tiempo_asignado,
                'curso_academico': instance.curso_academico,
            }
        )
        tiempo._sincronizando = True
        tiempo.save()
    else:
        for sustituto in prof.sustitutos.all():
            tiempo, created = TiempoGuardia.objects.update_or_create(
                profesor=sustituto,
                dia_semana=instance.dia_semana,
                tramo=instance.tramo,
                item_guardia=instance.item_guardia,
                defaults={
                    'tiempo_asignado': instance.tiempo_asignado,
                    'curso_academico': instance.curso_academico,
                }
            )
            tiempo._sincronizando = True
            tiempo.save()

@receiver(post_delete, sender=TiempoGuardia)
def eliminar_tiempo_guardia_sincronizado(sender, instance, **kwargs):
    prof = instance.profesor
    if prof is None:
        return
    if prof.SustitutoDe:
        TiempoGuardia.objects.filter(
            profesor=prof.SustitutoDe,
            dia_semana=instance.dia_semana,
            tramo=instance.tramo,
            item_guardia=instance.item_guardia,
            curso_academico=instance.curso_academico,
        ).delete()
    else:
        for sustituto in prof.sustitutos.all():
            TiempoGuardia.objects.filter(
                profesor=sustituto,
                dia_semana=instance.dia_semana,
                tramo=instance.tramo,
                item_guardia=instance.item_guardia,
                curso_academico=instance.curso_academico,
            ).delete()
