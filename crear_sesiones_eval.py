# Este código para poder usar ORM de django
import os
from collections import defaultdict
from datetime import time

import django
from django.db.models import Q


# Especifica la configuración de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion.settings')

# Inicializa Django
django.setup()

from centro.utils import get_current_academic_year
from centro.models import Profesores, MateriaImpartida, Cursos

class Bloque(object):
    hora_inicio = None
    hora_fin = None
    aula = None
    unidades = []

    def __init__(self, hora_inicio, hora_fin, aula, unidades):
        self.hora_inicio = hora_inicio
        self.hora_fin = hora_fin
        self.aula = aula
        self.unidades = unidades



def calcular_equipo_educativo(unidades):
    materias_impartidas = MateriaImpartida.objects.filter(curso__Curso__in=unidades, curso_academico=get_current_academic_year())
    equipo_educativo = defaultdict(list)
    for materia in materias_impartidas:
        equipo_educativo[materia.profesor].append((materia.materia, materia.curso))
    return equipo_educativo

def calcular_intersecciones(eq_1, eq_2):
    profes_1 = set(eq_1.keys())
    profes_2 = set(eq_2.keys())
    intersecciones = profes_1.intersection(profes_2)
    return intersecciones

if __name__ == '__main__':
    bloques_unidades = [
        ('1º ESO A', '1º ESO B'), ('1º ESO C', '1º ESO D'),
        ('2º ESO A', '2º ESO B'), ('2º ESO C', '2º ESO D'),
        ('3º ESO A',), ('3º ESO B',), ('3º ESO C',), ('3º ESO D',), ('3º ESO E',),
        ('4º ESO A',), ('4º ESO B',), ('4º ESO C',), ('4º ESO D',),
        ('1º BTO A',), ('1º BTO B',), ('1º BTO C',), ('1º BTO D',),
        ('2º BTO A',), ('2º BTO B',), ('2º BTO C',),
        ('1º SMR',), ('2º SMR',), ('1º ASIR',), ('2º ASIR',)
    ]
    sesiones = {
        '07/10/2025': [],
        '14/10/2025': [],
    }

    # Cargar equipos educativos de cada bloque
    equipos_educativos = {bloque: calcular_equipo_educativo(bloque) for bloque in bloques_unidades}
    bq_1 = ('4º ESO B',)
    bq_2 = ('4º ESO A',)
    eq_1 = equipos_educativos[bq_1]
    eq_2 = equipos_educativos[bq_2]
    unidades_implicadas = [Cursos.objects.filter(Curso=unidad).first() for unidad in bq_1 + bq_2]
    tutores = {unidad.Tutor: unidad for unidad in unidades_implicadas}

    for profesor in calcular_intersecciones(eq_1, eq_2):
        docencia = [f'{materia.abr}({curso.Curso})' for (materia, curso) in eq_1[profesor]]
        docencia.extend([f'{materia.abr}({curso.Curso})' for (materia, curso) in eq_2[profesor]])
        if profesor in tutores:
            docencia.append(f'TUT({tutores[profesor]})')

        print(f'{profesor.Nombre} {profesor.Apellidos}: {', '.join(docencia)}')
    # Calcular todas las distribuciones posibles
    # Evaluar cada distribución
    # Mostrar la mejor puntuada
