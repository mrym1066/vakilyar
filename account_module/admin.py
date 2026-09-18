from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_active', 'is_approved', 'is_staff']
    list_filter = ['is_active', 'is_approved', 'is_staff']
    list_editable = ['is_approved']
    
    fieldsets = UserAdmin.fieldsets + (
        ('اطلاعات اضافی', {'fields': ('avatar', 'about_user', 'address', 'is_approved')}),
    )

    actions = ['approve_users', 'reject_users']

    def approve_users(self, request, queryset):
        queryset.update(is_approved=True, is_active=True)
        self.message_user(request, 'کاربران انتخاب شده تأیید شدند.')
    approve_users.short_description = 'تأیید کاربران انتخاب شده'

    def reject_users(self, request, queryset):
        queryset.update(is_approved=False, is_active=False)
        self.message_user(request, 'کاربران انتخاب شده رد شدند.')
    reject_users.short_description = 'رد کاربران انتخاب شده'