# contact_module/admin.py

from django.contrib import admin
from .models import ContactUs, ContactPhoneNumber

class ContactPhoneNumberInline(admin.TabularInline):
    model = ContactPhoneNumber
    extra = 1

@admin.register(ContactUs)
class ContactUsAdmin(admin.ModelAdmin):
    inlines = [ContactPhoneNumberInline]


