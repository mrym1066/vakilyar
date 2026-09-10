from django.db import models
from jalali_date import date2jalali
from account_module.models import User
from .mixins import AutoSlugMixin # type: ignore


class ArticleCategory(models.Model,AutoSlugMixin):
    parent = models.ForeignKey('ArticleCategory', null=True, blank=True, on_delete=models.CASCADE, verbose_name='دسته بندی والد')
    title = models.CharField(max_length=200, verbose_name='عنوان دسته بندی')
    url_title = models.CharField(max_length=200, unique=True, verbose_name='عنوان در url')
    is_active = models.BooleanField(default=True, verbose_name='فعال / غیرفعال')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'دسته بندی مقاله'
        verbose_name_plural = 'دسته بندی های مقاله'


class Article(models.Model):
    title = models.CharField(max_length=300, verbose_name='عنوان مقاله')
    image = models.ImageField(upload_to='images/articles', verbose_name='تصویر مقاله')
    short_description = models.TextField(verbose_name='توضیحات کوتاه')
    pdf_file = models.FileField(upload_to='files/articles/pdf/', verbose_name='فایل PDF', null=True, blank=True)
    word_file = models.FileField(upload_to='files/articles/word/', verbose_name='فایل Word', null=True, blank=True)
    selected_categories = models.ManyToManyField(ArticleCategory, verbose_name='دسته بندی ها')
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='نویسنده', null=True, editable=False)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'مقاله'
        verbose_name_plural = 'مقالات'




