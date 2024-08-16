import csv
from pathlib import Path
from django.core.management.base import BaseCommand
from centro.utils import importar_profesores, importar_cursos


class Command(BaseCommand):
    help = 'Importar cursos desde un archivo CSV'

    def add_arguments(self, parser):
        parser.add_argument('csv_file_path', type=str, help='Ruta del archivo CSV de unidades')
        parser.add_argument('csv_file_path2', type=str, help='Ruta del archivo CSV de equipo educativo')

    def handle(self, *args, **kwargs):
        csv_file_path = kwargs['csv_file_path']
        csv_file_path2 = kwargs['csv_file_path2']
        importar_cursos(csv_file_path, csv_file_path2)
        self.stdout.write(self.style.SUCCESS('Importación de cursos completada'))
