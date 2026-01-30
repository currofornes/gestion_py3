# Este código para poder usar ORM de django
import os
from collections import defaultdict

import django

# Especifica la configuración de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion.settings')

# Inicializa Django
django.setup()

from centro.models import Centros, InfoAlumnos, CursoAcademico, Niveles
from convivencia.models import Amonestaciones

CARLOS_I = Centros.objects.filter(Codigo='41602077').first()
ORIPPO = Centros.objects.filter(Codigo='41602296').first()
IBARBURU = Centros.objects.filter(Codigo='41010371').first()
MONTECILLOS = Centros.objects.filter(Codigo='41010629').first()

CURSO_2425 = CursoAcademico.objects.filter(año_inicio=2024).first()
CURSO_2324 = CursoAcademico.objects.filter(año_inicio=2023).first()
CURSO_2223 = CursoAcademico.objects.filter(año_inicio=2022).first()
CURSO_2122 = CursoAcademico.objects.filter(año_inicio=2021).first()

ESO_1 = Niveles.objects.filter(Abr='1º ESO').first()
ESO_2 = Niveles.objects.filter(Abr='2º ESO').first()
ESO_3 = Niveles.objects.filter(Abr='3º ESO').first()
ESO_4 = Niveles.objects.filter(Abr='4º ESO').first()

def centro_origen(alumno):
    info = InfoAlumnos.objects.filter(Alumno=alumno).exclude(CentroOrigen__isnull=True).first()
    if info:
        return info.CentroOrigen
    else:
        return None

def total_alumnado(curso_academico):
    return InfoAlumnos.objects.filter(curso_academico=curso_academico).count()

def total_alumnado_origen(curso_academico, origen):
    info_alumnado = InfoAlumnos.objects.filter(curso_academico=curso_academico).all()
    count = 0
    for info in info_alumnado:
        if centro_origen(info.Alumno) == origen:
            count += 1
    return count

def total_amonestaciones(curso_academico):
    return Amonestaciones.objects.filter(curso_academico=curso_academico).count()

def total_amonestaciones_origen(curso_academico, origen):
    info_alumnado = InfoAlumnos.objects.filter(curso_academico=curso_academico).all()
    count = 0
    for info in info_alumnado:
        alumno = info.Alumno
        if centro_origen(alumno) == origen:
            count += Amonestaciones.objects.filter(IdAlumno=alumno, curso_academico=curso_academico).count()
    return count

if __name__ == '__main__':
    # for curso_academico in (CURSO_2122, CURSO_2223, CURSO_2324, CURSO_2425):
    #     total = total_alumnado(curso_academico)
    #     total_am = total_amonestaciones(curso_academico)
    #     print(f'Total alumnado en el curso {curso_academico}: {total} [{total_am} amonestaciones]')
    #     for origen in (CARLOS_I, ORIPPO, IBARBURU, MONTECILLOS):
    #         parte = total_alumnado_origen(curso_academico, origen)
    #         parte_am = total_amonestaciones_origen(curso_academico, origen)
    #         print(f'\t Alumnado del {origen}: {parte} ({100 * parte / total:.2f}%) [{parte_am} amonestaciones ({100 * parte_am / total_am:.2f}%)]' )

    errores = []
    for amonestacion in Amonestaciones.objects.filter(curso_academico=CURSO_2425).all():
        alumno = amonestacion.IdAlumno

        if not centro_origen(alumno):
            if alumno not in errores:
                errores.append(alumno)

    errores.sort(key=lambda x: x.Nombre)
    for alumno in errores:
        print(alumno.Nombre)