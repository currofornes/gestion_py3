from django.apps import AppConfig


class GuardiasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'guardias'
    icon_name = 'schedule'

    def ready(self):
        import guardias.signals