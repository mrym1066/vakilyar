from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Movakel
from contact_module.models import ContactUs


# handle_logical_delete حذف شد — تکراری بود.
# Movakel.delete() خودش با transaction.atomic() این کار را انجام می‌دهد:
#   MovakelPayment.objects.filter(movakel=self).update(is_delete=True)
# داشتن signal موازی علاوه بر double-query، اگر کسی مستقیم
# Movakel.all_objects.filter(...).update(is_delete=True) صدا بزند
# signal اجرا نمی‌شود ولی delete() همیشه اجرا می‌شود — پس منطق
# باید فقط در یک جا باشد.


@receiver(post_save, sender=Movakel)
def create_or_update_contact_us(sender, instance, created, update_fields=None, **kwargs):
    """
    وقتی موکل ذخیره می‌شود، یک رکورد ContactUs (دفترچه تلفن) متناظر
    ساخته یا به‌روزرسانی می‌شود.

    بهینه‌سازی: اگر save() فقط فیلدهای بی‌ربط به شماره تماس را ذخیره
    می‌کند (مثل add_case_step یا update_fields=['case_status'])،
    کوئری‌های اضافی زده نمی‌شود.
    """
    if update_fields is not None and 'mobile_number' not in update_fields:
        return

    if not instance.mobile_number:
        return

    # اگر بیش از یک رکورد مرتبط وجود داشت (داده تکراری قدیمی)، پاک‌سازی کن
    contacts = ContactUs.objects.filter(client=instance)
    if contacts.count() > 1:
        keep_id = contacts.order_by('id').first().id
        contacts.exclude(id=keep_id).delete()

    contact, contact_created = ContactUs.objects.get_or_create(
        client=instance,
        defaults={'client_phone_number': instance.mobile_number},
    )

    if not contact_created and contact.client_phone_number != instance.mobile_number:
        contact.client_phone_number = instance.mobile_number
        contact.save(update_fields=['client_phone_number'])
