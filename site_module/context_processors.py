from .models import SiteSetting


def site_setting(request):
    """
    تنظیمات سایت را در همه تمپلیت‌ها در دسترس قرار می‌دهد.
    بدون این، site_setting.site_name و مشابه در header خطا می‌دهند.
    """
    setting = SiteSetting.objects.filter(is_main_setting=True).first()
    return {
        'site_setting': setting
    }
