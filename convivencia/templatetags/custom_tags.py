from django import template

from centro.models import Cursos

register = template.Library()

@register.simple_tag
def is_tutor_curso(user, curso_id):
    """
    Determina si el usuario es tutor de un curso específico.
    """
    if user.is_authenticated and hasattr(user, 'profesor'):
        profesor = user.profesor
        # Comprobar si el profesor es tutor del curso con el id proporcionado
        return Cursos.objects.filter(Tutor_id=profesor.id, id=curso_id).exists()
    return False