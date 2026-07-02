from django.apps import AppConfig

class AgendaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.agenda'

    def ready(self) -> None:
        # Importa os signals para registrá-los no framework
        import apps.agenda.signals
