import csv
from pathlib import Path
from django.core.management.base import BaseCommand
from centro.utils import importar_profesores

class Command(BaseCommand):
    help = 'Importar datos de profesores desde un archivo CSV'

    def add_arguments(self, parser):
        parser.add_argument('csv_file_path', type=str, help='Ruta del archivo CSV')

    def handle(self, *args, **kwargs):
        csv_file_path = kwargs['csv_file_path']
        importar_profesores(csv_file_path)
        self.stdout.write(self.style.SUCCESS('Importación de profesores completada'))
