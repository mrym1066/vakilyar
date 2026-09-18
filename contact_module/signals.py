from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import ContactUs


@receiver(pre_save, sender=ContactUs)
def set_client_details(sender, instance, **kwargs):
    """
    قبل از ذخیره ContactUs، اگر موکل انتخاب شده باشد،
    شماره همراه را از مدل موکل می‌گیرد.

    توجه: این signal مکمل create_or_update_contact_us در movakel_module/signals.py
    است، نه جایگزین آن. آن signal موقع ذخیره موکل فعال می‌شود؛
    این signal موقع ذخیره مستقیم ContactUs از پنل ادمین.
    تضادی بین این دو وجود ندارد چون روی sender های متفاوت هستند.
    """
    if instance.client and instance.client.mobile_number:
        instance.client_phone_number = instance.client.mobile_number
