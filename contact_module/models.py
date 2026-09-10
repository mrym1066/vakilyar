from movakel_module.models import Movakel  # برای واردات مدل Movakel
from django.db import models



class ContactUs(models.Model):
    # اضافه کردن فیلدهای مربوط به موکل
    client = models.ForeignKey(Movakel, on_delete=models.CASCADE, verbose_name='مراجعه کننده', null=True, blank=True)
    client_phone_number = models.CharField(max_length=15, verbose_name='شماره همراه', null=True, blank=True)
    contact_name = models.CharField(max_length=300, verbose_name='نام و نام خانوادگی( عدم وکالت ) ', null=True, blank=True)  # نام اختیاری
    
    class Meta:
        verbose_name = 'شماره تماس موکل'
        verbose_name_plural = 'دفترچه تلفن موکلین'
    def __str__(self):
        # بررسی اینکه آیا client موجود است یا خیر
        if self.client:
            if self.contact_name:
                return f"{self.contact_name} - {self.client.name} - {self.client_phone_number if self.client_phone_number else 'شماره تماس موجود نیست'}"
            else:
                return f"{self.client.name} - {self.client_phone_number if self.client_phone_number else 'شماره تماس موجود نیست'}"
        else:
            # اگر client وجود نداشته باشد، نام و شماره تماس را خالی نمایش دهیم یا مقدار پیش‌فرض بگذاریم
            return f"وکالت داده نشده - {self.contact_name if self.contact_name else 'نام تماس موجود نیست'} - {self.client_phone_number if self.client_phone_number else 'شماره تماس موجود نیست'}"

    def save(self, *args, **kwargs):
        # اگر موکل وجود نداشته باشد و نام تماس گیرنده خالی باشد، مقدار پیش‌فرض قرار بده
        if not self.client and not self.contact_name:
            self.contact_name = "وکالت داده نشده"

        # اگر موکل انتخاب شده ولی شماره موبایل ست نشده، موبایل موکل را ست کن
        if self.client and not self.client_phone_number:
            self.client_phone_number = self.client.mobile_number

        super().save(*args, **kwargs)


class ContactPhoneNumber(models.Model):
    contact = models.ForeignKey(ContactUs, on_delete=models.CASCADE, verbose_name='تماس مربوط به')
    phone_number = models.CharField(max_length=15, verbose_name='شماره تماس')

    class Meta:
        verbose_name = 'شماره تماس اضافی'
        verbose_name_plural = 'شماره تماس‌های اضافی'

    def __str__(self):
        return self.phone_number