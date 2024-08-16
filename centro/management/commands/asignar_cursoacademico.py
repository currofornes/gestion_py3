import csv
from pathlib import Path
from django.core.management.base import BaseCommand
from centro.utils import importar_profesores, asignar_curso_academico


class Command(BaseCommand):
    help = 'Asignar curso académico a datos antiguos'

    def add_arguments(self, parser):
        parser.add_argument('cursoacademico_id', type=int, help='ID del curso académico')

    def handle(self, *args, **kwargs):
        cursoacademico_id = kwargs['cursoacademico_id']
        asignar_curso_academico(cursoacademico_id)
        self.stdout.write(self.style.SUCCESS('Asignación de curso académico completada'))
