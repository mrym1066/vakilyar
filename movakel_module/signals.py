from django.db.models.signals import post_save,pre_save
from django.dispatch import receiver
from .models import Movakel, MovakelPayment,RequestMeeting
from contact_module.models import ContactUs  # وارد کردن مدل ContactUs

@receiver(post_save, sender=Movakel)
def handle_logical_delete(sender, instance, **kwargs):
    """
    اگر پرونده به صورت منطقی حذف شد (is_delete=True)، پرداخت‌های مرتبط نیز حذف منطقی شوند.
    """
    if instance.is_delete:
        instance.movakelpayments.update(is_delete=True)


#@receiver(pre_save, sender=RequestMeeting)
def change_status_to_movakel(sender, instance, **kwargs):
    # زمانی که وضعیت تغییر کند و به وکالت تبدیل شده باشد
    if instance.status == 'converted' and not instance.related_movakel:
        instance.related_movakel = Movakel.objects.create(
            # ایجاد موکل جدید یا تنظیم اطلاعات موجود
        )


@receiver(post_save, sender=Movakel)
def create_or_update_contact_us(sender, instance, created, **kwargs):
    if instance.mobile_number:  # اگر شماره همراه موجود باشد
        # همه ContactUs های قبلی مرتبط با این موکل رو حذف کن (بجز یکی)
        contacts = ContactUs.objects.filter(client=instance)
        if contacts.count() > 1:
            contacts.exclude(id=contacts.first().id).delete()  # فقط یکی رو نگه دار

        contact, created = ContactUs.objects.get_or_create(
            client=instance,
            defaults={'client_phone_number': instance.mobile_number}
        )
        
        if not created:
            contact.client_phone_number = instance.mobile_number
            contact.save()
