from django.core.management.base import BaseCommand
from django.utils.text import slugify
from uuid import uuid4
from movakel_module.models import Movakel

class Command(BaseCommand):
    help = 'اصلاح مقادیر تکراری یا خالی در فیلد slug مدل Movakel'

    def handle(self, *args, **kwargs):
        for obj in Movakel.objects.all():
            if not obj.slug or Movakel.objects.filter(slug=obj.slug).count() > 1:
                base_slug = slugify(obj.title)
                unique_suffix = str(uuid4())[:8]  # ایجاد مقدار یکتا
                obj.slug = f"{base_slug}-{unique_suffix}"
                obj.save()
                self.stdout.write(self.style.SUCCESS(f'Slug updated for {obj.title}'))
