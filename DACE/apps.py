from django.apps import AppConfig


class DaceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'DACE'

    def ready(self):
        import DACE.signals
