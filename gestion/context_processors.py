from centro.models import Cursos


def is_tutor(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'profesor'):
            profesor = request.user.profesor
            return {'is_tutor': Cursos.objects.filter(Tutor_id=profesor.id).exists()}
    return {'is_tutor': False}