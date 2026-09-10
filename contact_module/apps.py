from django.apps import AppConfig


class ContactModuleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'contact_module'
    verbose_name = 'ماژول دفترچه تلفن  '
    
    def ready(self):
        import contact_module.signals  # وارد کردن سیگنال‌ها