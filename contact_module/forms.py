# contact_module/forms.py
from django import forms
from .models import ContactUs, ContactPhoneNumber

class ContactUsForm(forms.ModelForm):
    phone_number = forms.CharField(max_length=15, required=False, label="شماره تماس")

    class Meta:
        model = ContactUs
        fields = ['client', 'contact_name', 'phone_number']

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if commit:
            instance.save()
            
            # اگر کاربر موکل انتخاب کرده
            if instance.client:
                ContactPhoneNumber.objects.create(contact=instance, phone_number=instance.client.mobile_number)
            else:
                # اگر موکل انتخاب نکرده، شماره‌ای که وارد شده را ذخیره کن
                phone_number = self.cleaned_data.get('phone_number')
                if phone_number:
                    ContactPhoneNumber.objects.create(contact=instance, phone_number=phone_number)
        
        return instance
