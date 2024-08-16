import csv
from pathlib import Path
from django.core.management.base import BaseCommand
from centro.utils import importar_profesores, asignar_curso_academico, asignar_superusuario, crear_grupo


class Command(BaseCommand):
    help = 'Crear grupo de usuarios'

    def add_arguments(self, parser):
        parser.add_argument('groupname', type=str, help='Nombre del grupo a crear')

    def handle(self, *args, **kwargs):
        groupname = kwargs['groupname']
        crear_grupo(groupname)

        self.stdout.write(self.style.SUCCESS('Creación de grupo completada'))
