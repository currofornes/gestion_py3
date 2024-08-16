from django.apps import AppConfig


class AbsentismoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'absentismo'
    icon_name = 'contact_mail'

    def ready(self):
        import absentismo.signals  # Importa el archivo de signals
