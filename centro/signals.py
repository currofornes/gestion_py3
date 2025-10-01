from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from centro.models import RevisionLibroAlumno, CursoAcademico, RevisionLibro, PreferenciaHorario, Materia, \
    MateriaImpartida, MatriculaMateria, Profesores, Cursos
from centro.utils import get_current_academic_year

@receiver(pre_save, sender=RevisionLibro)
@receiver(pre_save, sender=PreferenciaHorario)
@receiver(pre_save, sender=Materia)
@receiver(pre_save, sender=MateriaImpartida)
@receiver(pre_save, sender=MatriculaMateria)
def asignar_curso_academico(sender, instance, **kwargs):
    if not instance.curso_academico:
        try:
            curso_actual = get_current_academic_year()
            instance.curso_academico = curso_actual
        except CursoAcademico.DoesNotExist:
            instance.curso_academico = None  # O lanza una excepción si lo prefieres

@receiver(post_save, sender=Profesores)
def reasignar_dependencias_profesor(sender, instance, created, **kwargs):
    # Solo al crear un sustituto
    if created and instance.SustitutoDe:
        titular = instance.SustitutoDe

        # Reasignar tutorías de cursos
        cursos_a_reasignar = Cursos.all_objects.filter(Tutor=titular)
        for curso in cursos_a_reasignar:
            curso.Tutor = instance
            curso.save(update_fields=["Tutor"])

        # Reasignar materias impartidas (en todos los años)
        materias_a_reasignar = MateriaImpartida.objects.filter(profesor=titular)
        for materia in materias_a_reasignar:
            materia.profesor = instance
            materia.save(update_fields=["profesor"])




