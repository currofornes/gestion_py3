from django.apps import AppConfig


class ConvivenciaConfig(AppConfig):
    name = 'convivencia'
    icon_name = 'sentiment_very_dissatisfied'

    def ready(self):
        import convivencia.signals  # Importa el archivo de signals
