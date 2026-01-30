from analres.models import Calificaciones


def calcular_tasa_exito(curso, campana, centro, materia):
    """
    Calcula el porcentaje de aprobados (>=5).
    Adapta la búsqueda a múltiples niveles usando __in.
    """
    # 1. Obtenemos la lista de IDs de los niveles asociados a la campaña
    # Esto es necesario porque campana.niveles es un QuerySet
    niveles_ids = campana.niveles.values_list('id', flat=True)

    filtros = {
        'curso_academico': curso,

        # CAMBIO CLAVE: Usamos 'Nivel__in' en lugar de 'Nivel'
        # Esto buscará calificaciones cuyo nivel esté DENTRO de los niveles de la campaña
        'Nivel__in': niveles_ids,

        'Alumno__info_adicional__Repetidor': False,
        'Materia': materia.abr,
    }

    if centro is not None:
        filtros['Alumno__info_adicional__CentroOrigen'] = centro

    qs = Calificaciones.objects.filter(**filtros).exclude(Calificacion='')

    total_validos = 0
    total_aprobados = 0

    for registro in qs:
        nota_str = registro.Calificacion
        try:
            valor = float(nota_str)
            total_validos += 1
            if valor >= 5:
                total_aprobados += 1
        except (ValueError, TypeError):
            continue

    if total_validos == 0:
        return None

    return (total_aprobados / total_validos) * 100