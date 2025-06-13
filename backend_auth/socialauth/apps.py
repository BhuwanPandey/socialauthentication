from django.apps import AppConfig


class SocialauthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'socialauth'

    def ready(self):
        import socialauth.signals  # noqa: F401
