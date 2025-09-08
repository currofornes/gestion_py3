from django.apps import AppConfig


class HorariosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'horarios'
    icon_name = 'event_note'

    def ready(self):
        import horarios.signals  # Importa el archivo de signals
