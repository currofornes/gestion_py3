import csv
from pathlib import Path
from django.core.management.base import BaseCommand
from centro.utils import importar_profesores, asignar_curso_academico, asignar_superusuario


class Command(BaseCommand):
    help = 'Asignar curso académico a datos antiguos'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='username del usuario a asignar')

    def handle(self, *args, **kwargs):
        username = kwargs['username']
        asignar_superusuario(username)

        self.stdout.write(self.style.SUCCESS('Asignación de superusuario completada'))
