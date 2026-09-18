from django.apps import AppConfig


class MovakelModuleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'movakel_module'
    verbose_name = 'ماژول پرونده'

    def ready(self):
        import movakel_module.signals
