from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import SiteSetting
from .context_processors import CACHE_KEY


@receiver(post_save, sender=SiteSetting)
@receiver(post_delete, sender=SiteSetting)
def clear_site_setting_cache(sender, **kwargs):
    """
    با هر ذخیره/حذف SiteSetting از پنل ادمین، کش تنظیمات سایت پاک می‌شود
    تا تغییرات فوراً در همه صفحات سایت دیده شوند (نه بعد از یک ساعت).
    """
    cache.delete(CACHE_KEY)
