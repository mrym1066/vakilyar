from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import ContactUs

@receiver(pre_save, sender=ContactUs)
def set_client_details(sender, instance, **kwargs):
    if instance.client:  # اگر موکل مشخص باشد
        instance.client_phone_number = instance.client.mobile_number  # شماره همراه موکل را به صورت خودکار می‌گیریم
