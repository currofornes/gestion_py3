from django.apps import AppConfig


class CentroConfig(AppConfig):
    name = 'centro'
    icon_name = 'school'

    def ready(self):
        import centro.signals  # Importa el archivo de signals
