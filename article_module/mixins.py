# mixins.py
try:
    from slugify import slugify  # python-slugify — پشتیبانی فارسی
except ImportError:
    from django.utils.text import slugify


class AutoSlugMixin:
    """Auto-generate url_title from title using unicode-aware slugify"""
    def save(self, *args, **kwargs):
        if hasattr(self, 'title') and hasattr(self, 'url_title'):
            if not self.url_title:
                self.url_title = slugify(self.title, allow_unicode=True)
        super().save(*args, **kwargs)
