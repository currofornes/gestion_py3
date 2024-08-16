import csv
from pathlib import Path
from django.core.management.base import BaseCommand
from centro.utils import importar_profesores, asignar_curso_academico, asignar_superusuario, asignar_grupo


class Command(BaseCommand):
    help = 'Asignar grupo a un usuario'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='username del usuario a asignar')
        parser.add_argument('groupname', type=str, help='nombre del grupo a asignar')

    def handle(self, *args, **kwargs):
        username = kwargs['username']
        groupname = kwargs['groupname']
        asignar_grupo(username, groupname)

        self.stdout.write(self.style.SUCCESS('Asignación de grupo completada'))
