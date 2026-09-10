from django.core.management.base import BaseCommand
from movakel_module.models import MovakelPayment

class Command(BaseCommand):
    help = 'Clean payments related to logically deleted movakels'

    def handle(self, *args, **kwargs):
        # به‌روزرسانی پرداخت‌های مرتبط با پرونده‌های حذف‌شده
        payments_to_clean = MovakelPayment.objects.filter(movakel__is_delete=True)
        updated_count = payments_to_clean.update(is_delete=True)
        self.stdout.write(f"Successfully updated {updated_count} payments.")
