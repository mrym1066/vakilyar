from django.apps import AppConfig


class SiteModuleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'site_module'
    verbose_name = 'ماژول تنظیمات سایت'

    def ready(self):
        from . import signals  # noqa: F401 — فقط برای اتصال سیگنال‌ها import می‌شود
