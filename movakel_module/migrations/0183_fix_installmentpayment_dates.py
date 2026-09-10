"""
Migration برای اصلاح default تاریخ InstallmentPayment
jdatetime.date.today → datetime.date.today (سازگار با Django)
"""
import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('movakel_module', '0182_remove_movakel_service_type_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='installmentpayment',
            name='due_date',
            field=models.DateField(
                default=datetime.date.today,
                verbose_name='تاریخ سررسید'
            ),
        ),
        migrations.AlterField(
            model_name='installmentpayment',
            name='payment_date',
            field=models.DateField(
                null=True,
                blank=True,
                verbose_name='تاریخ پرداخت'
            ),
        ),
        migrations.AlterField(
            model_name='requestmeeting',
            name='national_id',
            field=models.CharField(
                max_length=10,
                verbose_name='کد ملی',
                db_index=True
            ),
        ),
    ]
