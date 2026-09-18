# حذف فیلد email_active_code
# این فیلد فقط توسط فلوی «فراموشی رمز عبور» و «فعال‌سازی از طریق ایمیل» استفاده می‌شد
# که هر دو حذف شدن؛ بازیابی رمز عبور حالا فقط از پنل ادمین انجام می‌شه.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account_module', '0007_add_is_approved'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='email_active_code',
        ),
    ]
