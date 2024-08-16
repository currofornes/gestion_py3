import csv
from pathlib import Path
from django.core.management.base import BaseCommand
from centro.utils import importar_profesores, importar_alumnos


class Command(BaseCommand):
    help = 'Importar datos de alumnos desde un archivo CSV'

    def add_arguments(self, parser):
        parser.add_argument('csv_file_path', type=str, help='Ruta del archivo CSV')
        parser.add_argument('borrar_alumnos', type=bool, help='Opcion borrar alumnos')

    def handle(self, *args, **kwargs):
        csv_file_path = kwargs['csv_file_path']
        borrar_alumnos = kwargs['borrar_alumnos']
        importar_alumnos(csv_file_path, borrar_alumnos)
        self.stdout.write(self.style.SUCCESS('Importación de alumnos completada'))
