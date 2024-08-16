from django.apps import AppConfig


class TdeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tde'
    icon_name = 'new_releases'

    def ready(self):
        import tde.signals
