from django.core.cache import cache

from .models import SiteSetting

CACHE_KEY = 'site_module:main_site_setting'
CACHE_TIMEOUT = 60 * 60  # ۱ ساعت — با سیگنال save/delete هم فوراً پاک می‌شود


def site_setting(request):
    """
    تنظیمات سایت را در همه تمپلیت‌ها در دسترس قرار می‌دهد.
    بدون این، site_setting.site_name و مشابه در header خطا می‌دهند.

    نکته کارایی: این تابع روی *هر* درخواست هر صفحه‌ای از سایت اجرا می‌شود،
    پس نتیجه کش می‌شود تا به‌ازای هر بازدید یک کوئری اضافه به دیتابیس زده نشود.
    کش با سیگنال‌های post_save/post_delete در models.py بلافاصله پس از تغییر
    تنظیمات از پنل ادمین، باطل (invalidate) می‌شود.
    """
    setting = cache.get(CACHE_KEY)
    if setting is None:
        setting = SiteSetting.objects.filter(is_main_setting=True).first()
        cache.set(CACHE_KEY, setting, CACHE_TIMEOUT)
    return {
        'site_setting': setting
    }
