from datetime import timedelta, date, datetime, time
from django.db import models, transaction
from django.urls import reverse
from account_module.models import User
from django.utils import timezone
import uuid
from jalali_date import date2jalali, datetime2jalali
from django.shortcuts import redirect
from django.core.validators import RegexValidator
from django.apps import apps
import jdatetime
import datetime
from django.utils.timezone import make_aware, now
from django.db.models import Sum
from decimal import Decimal
import os
from slugify import slugify  # python-slugify — پشتیبانی از فارسی
from django_jalali.db import models as jmodels
from jdatetime import date as jdate


# Create your models here.
# Choices برای روش‌های پرداخت
PAYMENT_METHOD_CHOICES = [
    ('cash', 'نقدی'),
    ('check', 'چک'),
    ('card', 'کارت به کارت'),
    ('pos', 'دستگاه پز'),
    ('bank_transfer', 'انتقال بانکی'),
    ('credit_card', 'کارت اعتباری'),
]

PAYMENT_FOR_CHOICES = [
    ("lawsuit", "هزینه دادرسی"),
    ("document", "هزینه تنظیم سند"),
    ("undergraduate fee", "هزینه کارشناسی"),
    ("other", "سایر هزینه‌ها"),
]


def upload_to_movakel(instance, filename):
    """بر اساس سال وکالت مسیر ذخیره فایل را مشخص می‌کند"""
    year = instance.contract_date.year if instance.contract_date else now().year
    return os.path.join(f'movakels/{year}/', filename)


# ShamsiDateMixin فقط از mixins.py وارد می‌شود — تعریف تکراری حذف شد
class ShamsiDateMixin(models.Model):
    """Abstract mixin برای نمایش تاریخ شمسی"""
    class Meta:
        abstract = True

    @property
    def shamsi_date(self):
        if hasattr(self, 'date') and isinstance(self.date, (datetime.date, datetime.datetime)):
            return jdatetime.date.fromgregorian(date=self.date).strftime('%Y/%m/%d')
        if hasattr(self, 'meeting_date') and isinstance(self.meeting_date, (datetime.date, datetime.datetime)):
            return jdatetime.date.fromgregorian(date=self.meeting_date).strftime('%Y/%m/%d')
        return "-"
    
class MovakelManager(models.Manager):
    def get_queryset(self):
        # فقط رکوردهایی که is_delete=False هستند را بازگرداند
        return super().get_queryset().filter(is_delete=False)

class MovakelCategory(models.Model):
    title = models.CharField(max_length=300, db_index=True, verbose_name='عنوان')
    url_title = models.CharField(max_length=300, db_index=True, verbose_name='عنوان در url', blank=True, null=True)

    def save(self, *args, **kwargs):
        # اگر url_title خالی است، آن را از روی title پر کنیم
        if not self.url_title:
            self.url_title = slugify(self.title, allow_unicode=True).replace('_', '-')
        super().save(*args, **kwargs)

    def __str__(self):
        return f'( {self.title} - {self.url_title} )'

    class Meta:
        verbose_name = 'دسته بندی'
        verbose_name_plural = 'دسته بندی ها'

class PDFFile(models.Model):
    name = models.CharField(max_length=255, verbose_name="نام فایل")
    file = models.FileField(upload_to='pdfs/', verbose_name="فایل PDF")
    uploaded_at = models.DateTimeField (auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'فایل pdf '
        verbose_name_plural = '  فایل های pdf'

class Branch(models.Model):
    name = models.CharField(max_length=255, verbose_name="نام شعبه")
    category = models.CharField(max_length=255, verbose_name="نوع دسته‌بندی")

    def __str__(self):
        # نمایش اطلاعات شعبه به همراه شماره بایگانی در یک خط
        return f"شعبه  {self.name} {self.category}"
    
    class Meta:
        verbose_name = 'شعبه'
        verbose_name_plural = 'شعبات'


class ServiceType(models.Model):
    #movakel = models.ForeignKey('Movakel', on_delete=models.CASCADE, null=True, blank=False)  # Default to an existing Movakel id
    movakel = models.OneToOneField('Movakel',on_delete=models.CASCADE, related_name='service_type')
    office_study = models.BooleanField(default=False, blank=True, verbose_name="مطالعه پرونده")
    defense = models.BooleanField(default=False,  blank=True,verbose_name='دفاع')
    consultation = models.BooleanField(default=False,  blank=True,verbose_name='مشاوره')
    check_documents = models.BooleanField(default=False, blank=True, verbose_name='بررسی مدارک')
    contract = models.BooleanField(default=False, blank=True, verbose_name='تنظیم قراردهای متفرقه')
    notification = models.BooleanField(default=False, blank=True, verbose_name="اخذ ابلاغیه")
    bill = models.BooleanField(default=False, blank=True, verbose_name='لایحه')

    # هزینه‌های مربوط به اختیار وکیل
    
    travel_fee = models.DecimalField(max_digits=10, decimal_places=3, default=0, verbose_name="هزینه سفر(هتل ،وسیله نقلیه و غیره)")
    miscellaneous_fee = models.DecimalField(max_digits=10, decimal_places=3, default=0, verbose_name="هزینه های متفرقه(اوراق ، سی دی و غیره)")
    office_study_fee = models.DecimalField(max_digits=10, decimal_places=3, default=0, verbose_name="هزینه مطالعه پرونده")
    contract_fee = models.DecimalField(max_digits=10, decimal_places=3, default=0, verbose_name="هزینه تنظیم قراردهای متفرقه")

    # هزینه کلی برای خدمات وکیل
    lawyer_services_fee = models.DecimalField(max_digits=10, decimal_places=3, default=0, verbose_name='هزینه کل خدمات وکیل')

    # فیلدهای مربوط به هزینه دادرسی
    bill_fee = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True, verbose_name="هزینه ارسال لوایح", default=0)
    initial_fee = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True, verbose_name="هزینه دادرسی بدوی(تمبر دادرسی)", default=0)
    appeal_fee = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True, verbose_name="هزینه اعتراض(هزینه دادرسی)", default=0)
    enforcement_fee = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True, verbose_name="هزینه اجرای احکام", default=0)
    petition_fee = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True, verbose_name="هزینه تنظیم شکوائیه", default=0)
    court_service_fee = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True, verbose_name="هزینه دفتر خدمات قضائی", default=0)
    document_fee = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True, verbose_name="هزینه اظهارنامه", default=0)
    notification_fee = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True,verbose_name="هزینه اخذ ابلاغیه از سامانه",default=0)

    def get_selected_services(self):
        """برگرداندن لیست خدمات انتخاب شده"""
        selected_services = []
        if self.defense:
            selected_services.append("دفاع")
        if self.consultation:
            selected_services.append("مشاوره")
        if self.check_documents:
            selected_services.append("بررسی مدارک")
        if self.office_study:
            selected_services.append("مطالعه پرونده")
        if self.contract:
            selected_services.append("تنظیم قراردهای متفرقه")
        if self.notification:
            selected_services.append("اخذ ابلاغیه")
        if self.bill:
            selected_services.append("لایحه")
            
        return selected_services
    @property
    def total_fee(self):
        return (
            self.lawyer_services_fee +  # هزینه کلی خدمات وکیل
            (self.bill_fee or 0) + 
            (self.initial_fee or 0) + 
            (self.appeal_fee or 0) + 
            (self.enforcement_fee or 0) + 
            (self.petition_fee or 0) + 
            (self.court_service_fee or 0) + 
            (self.document_fee or 0)
        )
    # متد محاسبه جمع کل هزینه دادرسی
    def total_litigation_fees(self):
        return (
            (self.bill_fee or 0) + 
            (self.initial_fee or 0) + 
            (self.appeal_fee or 0) + 
            (self.enforcement_fee or 0) + 
            (self.petition_fee or 0) + 
            (self.court_service_fee or 0) + 
            (self.document_fee or 0)
        )
    def __str__(self):
        return str(self.movakel)

    class Meta:
        verbose_name = 'اقدام'
        verbose_name_plural = 'اقدامات'


class DefenseDocument(ShamsiDateMixin,models.Model):
    movakel = models.ForeignKey('Movakel', on_delete=models.CASCADE, related_name='defense_documents',verbose_name='موکل')
    stage = models.CharField(
        max_length=500,
        choices=[
        ('initial', 'بدوی'),
        ('appeal', 'تجدیدنظر'),
        ('execution', 'اجرای احکام'),
        ('petition', 'تنظیم لایحه'),
        ],
        verbose_name="مرحله"
    )

    subject = models.CharField(max_length=255, verbose_name="موضوع")  # اضافه کردن موضوع
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")    #mechanized_number = models.CharField(max_length=18, verbose_name="شماره مکانیزه", null=True, blank=True)  # اضافه کردن شماره مکانیزه
    pdf_file = models.FileField(upload_to='documents/pdf/', null=True, blank=True, verbose_name="فایل PDF")  # فایل PDF
    word_file = models.FileField(upload_to='documents/word/', null=True, blank=True, verbose_name="فایل Word")  # فایل Word
    slug = models.CharField(max_length=255, unique=True, blank=True, null=True, verbose_name='اسلاگ')

    @property
    def mechanized_number(self):
        return self.movakel.mechanized_number if self.movakel else None

    def __str__(self):
        return f"{self.movakel.full_name} - {self.stage}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = f"{self.movakel.full_name}-{self.get_stage_display()}"  # نمایش فارسی مرحله
            self.slug = base_slug.replace(" ", "-")  # فقط جایگزینی فاصله با -
        super().save(*args, **kwargs)

    def get_summary(self):
        """خلاصه موضوع لایحه — فیلد content وجود ندارد، از subject استفاده می‌شود"""
        return self.subject[:150] if self.subject else "-"

    def get_jalali_date(self):
        return datetime2jalali(self.created_at).strftime('%Y/%m/%d')  # نمایش YYYY/MM/DD
    
    class Meta:
        verbose_name = 'تنظیم لایحه'
        verbose_name_plural = 'تنظیم لایحه ها'

class Meeting(models.Model):
    full_name = models.CharField(max_length=100)
    national_id = models.CharField(max_length=10)
    phone_number = models.CharField(max_length=15)
    mobile_number = models.CharField(max_length=15)
    meeting_date = models.DateField()
    
    # فیلدهای جدید
    birth_date = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True, null=True)
    education = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=10, blank=True, null=True)
    
    # اگر تاریخ شمسی می‌خوای، متد جداگانه تعریف کن
    @property
    def birth_date_shamsi(self):
        if self.birth_date:
            return self.birth_date  # یا تبدیل به شمسی با کتابخانه‌ای مثل jdatetime
        return None
    
# مدل جداگانه برای موضوعات ملاقات
class MeetingSubject(models.Model):
    name = models.CharField(max_length=100, verbose_name="عنوان موضوع")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "موضوع ملاقات"
        verbose_name_plural = "موضوعات ملاقات"

class RequestMeeting(ShamsiDateMixin,models.Model):
    MEETING_TYPES = [
        ('phone', 'تلفنی'),
        ('in_person', 'حضوری'),
        ('online', 'آنلاین'),
    ]
    SUBJECT_CHOICES = [
        ('consultation', 'مشاوره'),
        ('lawsuit', 'لایحه'),
        ('document_review', 'بررسی مدارک'),
    ]
    STATUS_CHOICES = [
        ('pending', 'مشاوره'),
        ('converted', 'موکل'),
    ]
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="وضعیت درخواست"
    )
    movakel = models.ForeignKey('Movakel', on_delete=models.CASCADE, related_name='meetings', null=True, blank=True)
    full_name = models.CharField(max_length=255, verbose_name="نام و نام خانوادگی")
    national_id = models.CharField(max_length=10, verbose_name="کد ملی", db_index=True)
    identification_number = models.CharField(max_length=20, verbose_name="شماره شناسنامه", blank=True, null=True)  # 👈 اختیاری
    birth_date = models.DateField(verbose_name="تاریخ تولد", blank=True, null=True)  # 👈 اختیاری
    phone_number = models.CharField(max_length=11, verbose_name="تلفن ثابت", blank=True, null=True)  # 👈 اختیاری
    mobile_number = models.CharField(max_length=11, verbose_name="تلفن همراه")
    virtual_number = models.CharField(
        max_length=11,  # محدودیت حداکثر طول 11 رقم
        verbose_name="شماره فضای مجازی",
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\d{1,11}$',  # فقط اعداد و حداکثر 11 رقم
                message="شماره باید فقط شامل اعداد و حداکثر 11 رقم باشد."
            )
        ]
    )
    email = models.EmailField(verbose_name="نشانی اینترنتی", blank=True, null=True)  # 👈 اختیاری
    address = models.TextField(verbose_name="آدرس", blank=True, null=True)  # 👈 اختیاری
    postal_code = models.CharField(max_length=10, verbose_name="کدپستی", blank=True, null=True)  # 👈 اختیاری
    meeting_type = models.CharField(max_length=20, choices=MEETING_TYPES, verbose_name="نوع ملاقات")
    meeting_subject = models.ManyToManyField('MeetingSubject', verbose_name="موضوع ملاقات", blank=True)
    # حذف فیلدهای تاریخ؛ فقط فیلدهای زمان ورود و خروج نگه داشته می‌شوند
    start_time = models.TimeField(verbose_name="زمان ورود", null=True, blank=True)
    end_time = models.TimeField(verbose_name="زمان خروج", null=True, blank=True)
    meeting_date = models.DateTimeField(
        verbose_name="تاریخ ملاقات",
        null=True,
        blank=True
    )    
    created_at = models.DateTimeField (auto_now_add=True, verbose_name="زمان درخواست")
    meeting_fee = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, default=0,verbose_name="هزینه ملاقات")
    duration = models.CharField(max_length=50, blank=True, null=True, verbose_name="مدت جلسه")  # 👈 تغییر به CharField
    related_movakel = models.ForeignKey(
        'Movakel',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="related_request_meetings",  # تغییر نام related_name
        verbose_name="وکالت داده شده (سابقه مراجعه)"
    )
        # متدهای نمایش تاریخ شمسی
    @property
    def birth_date_shamsi(self):
        if self.birth_date:
            return jdatetime.date.fromgregorian(date=self.birth_date).strftime('%Y/%m/%d')
        return "-"
    

    def meeting_date_shamsi(self):
        if self.meeting_date:
            return jdatetime.date.fromgregorian(date=self.meeting_date).strftime('%Y/%m/%d')
        return ''

    @property
    def created_at_shamsi_pretty(self):
        if self.created_at:
            return jdatetime.datetime.fromgregorian(datetime=self.created_at).strftime('%Y/%m/%d %H:%M')
        return "-"
    
    def meeting_date_formatted(self):
        if self.meeting_date:
            # نمایش به صورت ساده بدون timezone
            return self.meeting_date.strftime('%Y-%m-%d %H:%M:%S')
        return "-"
    meeting_date_formatted.short_description = "تاریخ ملاقات"

    
    def save(self, *args, **kwargs):
        # محاسبه مدت زمان جلسه
        if self.start_time and self.end_time:
            today = datetime.date.today()
            start = datetime.datetime.combine(today, self.start_time)
            end = datetime.datetime.combine(today, self.end_time)
            duration = (end - start).seconds // 60
            self.duration = f"{duration} دقیقه" if duration > 0 else "کمتر از ۱ دقیقه"

        # تبدیل وضعیت به وکالت
        if self.status == 'converted' and not self.related_movakel:
            slug = slugify(self.full_name) or str(uuid.uuid4())[:10]
            self.related_movakel = Movakel.objects.create(
                name=self.full_name,
                mobile_number=self.mobile_number,
                file_number=self.phone_number,
                mechanized_number=str(uuid.uuid4())[:10],
                description=f"پرونده مربوط به {self.full_name}",
                is_active=True,
                slug=slug,
            )
            self.related_movakel.save()

        # حذف تبدیل تاریخ در این بخش - جنگو به صورت خودکار مدیریت می‌کند
        super().save(*args, **kwargs)

        # هدایت به صفحه جزئیات پس از تبدیل
        #if self.status == 'converted' and self.related_movakel and self.related_movakel.slug:
            #return redirect('movakel-detail', slug=self.related_movakel.slug)



    def __str__(self):
        return f"{self.full_name}"

    class Meta:
        verbose_name = "درخواست ملاقات"
        verbose_name_plural = "درخواست‌های ملاقات"


""" class HearingSchedule(ShamsiDateMixin,models.Model):
    movakel = models.ForeignKey('Movakel', on_delete=models.CASCADE, related_name='hearing_schedules')
    hearing_date = models.DateField(null=True, blank=True, verbose_name="تاریخ جلسه رسیدگی")
    hearing_time = models.TimeField(verbose_name="زمان رسیدگی")


    class Meta:
        verbose_name = "وقت رسیدگی"
        verbose_name_plural = "وقت‌های رسیدگی"
        ordering = ['hearing_date']

    def __str__(self):
        return f"{self.hearing_date} - {self.hearing_time}" """


class Expert(models.Model):
    name = models.CharField(max_length=300, verbose_name='نام کارشناس')
    mobile_number = models.CharField(max_length=11, verbose_name='شماره همراه', null=True, blank=True)
    expertise = models.CharField(max_length=255, verbose_name="تخصص", default="نامشخص")  # مقدار پیش‌فرض اضافه شد

    def __str__(self):
        return f" {self.name} - {self.expertise}"

    class Meta:
        verbose_name = 'کارشناس'
        verbose_name_plural = 'کارشناسان'



class Movakel(ShamsiDateMixin,models.Model):
    request_meeting = models.ForeignKey(RequestMeeting, on_delete=models.CASCADE, verbose_name="درخواست ملاقات", related_name="movakels", null=True, blank=True)
    name = models.CharField(max_length=300, verbose_name='نام موکل')
    national_id = models.CharField(max_length=10,verbose_name='کد ملی', blank=True, db_index=True)  # برای جستجوی سریع‌تر
    
    branchs = models.ManyToManyField(Branch, blank=True)  # آیا این فیلد وجود دارد؟
    category = models.ForeignKey(MovakelCategory, on_delete=models.SET_NULL,related_name='movakel_categories', null=True, blank=True,verbose_name='دسته‌بندی‌ها')
    image = models.ImageField(upload_to='images/movakels', null=True, blank=True, verbose_name='تصویر پرونده')
    pdf_files = models.ManyToManyField("PDFFile", blank=True, related_name="movakels", verbose_name="فایل‌های PDF")
    defensedocument_set = models.ManyToManyField(DefenseDocument, blank=True, related_name="movakels")
    #service_type = models.ForeignKey(ServiceType, on_delete=models.SET_NULL, null=True, blank=True,related_name='movakels',verbose_name=' اقدامات')
    presenter = models.CharField(max_length=300, null=True, verbose_name='معرف')
    age = models.CharField(max_length=3, verbose_name='سن')
    #price = models.DecimalField(max_digits=10, decimal_places=3, verbose_name='مبلغ پیش‌فرض')  # افزودن فیلد قیمت
    mobile_number = models.CharField(max_length=11, verbose_name='شماره همراه')
    file_number = models.CharField(max_length=11, null=True, verbose_name='شماره تلفن ثابت')
    mechanized_number = models.CharField(null=True, max_length=20, verbose_name='شماره مکانیزه')
    #archive_no = models.CharField(max_length=50, verbose_name="شماره بایگانی", null=True, blank=True)  # فیلد شماره بایگانی
    description = models.TextField(verbose_name='توضیحات اصلی', db_index=True)
    #slug = models.SlugField(default="", unique=True, null=False, blank=True, max_length=200, verbose_name='عنوان در URL')
    slug = models.SlugField(unique=True, blank=True, allow_unicode=True)
    is_active = models.BooleanField(default=False, verbose_name='فعال / غیرفعال')
    is_delete = models.BooleanField(default=False, verbose_name='حذف شده / نشده')
    CASE_STATUS_CHOICES = [
    ('in_progress', 'در جریان'),
    ('appeal', 'تجدیدنظر'),
    ('execution', 'اجرای حکم'),
    ('closed', 'مختومه'),
    ('archived', 'بایگانی'),
    ]
    case_status = models.CharField(
        max_length=20,
        choices=CASE_STATUS_CHOICES,
        default='in_progress',
        verbose_name='وضعیت پرونده'
    )
    
    objects = MovakelManager()  # مدیر سفارشی
    all_objects = models.Manager()  # دسترسی به تمام رکوردها (شامل حذف شده‌ها)   
    payment_method = models.CharField(
        max_length=50,
        choices=PAYMENT_METHOD_CHOICES,
        verbose_name='نحوه پرداخت',
        null=True,
        blank=True
    )
    final_result = models.TextField(null=True, blank=True, verbose_name="  ملاحظات")
    case_steps = models.JSONField(default=list, blank=True, verbose_name="مراحل پرونده")
    hearing_date = models.DateField(null=True, blank=True, verbose_name="وقت رسیدگی /وقت نظارت")
    hearing_time = models.TimeField(null=True, blank=True, verbose_name="زمان رسیدگی")  # زمان رسیدگی
    primary_archive_no = models.CharField(max_length=6, null=True, blank=True, verbose_name="شماره بایگانی بدوی")
    primary_court_number = models.CharField(max_length=20, null=True, blank=True, verbose_name="شماره دادنامه بدوی")
    primary_court_notification_date = models.DateField(null=True, blank=True, verbose_name="تاریخ ابلاغ بدوی")
    primary_court_result = models.TextField(null=True, blank=True, verbose_name="نتیجه رأی بدوی")
    appeal_archive_no = models.CharField(max_length=6, null=True, blank=True, verbose_name="شماره بایگانی تجدیدنظر")
    appeal_court_number = models.CharField(max_length=20, null=True, blank=True, verbose_name="شماره دادنامه تجدیدنظر")
    appeal_court_notification_date = models.DateField(null=True, blank=True, verbose_name="تاریخ ابلاغ تجدیدنظر")
    appeal_court_result = models.TextField(null=True, blank=True, verbose_name="نتیجه رأی تجدیدنظر")
    executive_archive_no = models.CharField(max_length=6, null=True, blank=True, verbose_name="شماره بایگانی اجرای احکام")
    executive_court_result = models.TextField(null=True, blank=True, verbose_name="عملیات اجرائی")
    executive_case_number = models.CharField(max_length=6, null=True, blank=True, verbose_name="شماره اجرائیه پرونده")
    executive_case_notification_date = models.DateField(null=True, blank=True, verbose_name="تاریخ ابلاغ اجرائیه پرونده")
    auction_date = models.DateField(null=True, blank=True, verbose_name="تاریخ مزایده")  # تاریخ مزایده
    total_amount = models.PositiveIntegerField(verbose_name="مبلغ کل حق الوکاله ", default=0)
    bail_amount = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        verbose_name="مبلغ وثیقه/کفالت (تومان)"
    )
    primary_branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name="primary_movakels", verbose_name="شعبه بدوی")
    appeal_branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name="appeal_movakels", verbose_name="شعبه تجدیدنظر")
    executive_branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name='executive_branches', verbose_name="شعبه اجرای احکام")

    # اضافه کردن ارتباط با کارشناسان
    expert = models.ManyToManyField(Expert, blank=True, related_name="movakels", verbose_name="کارشناس")
    
    #پرونده‌های موکلین بر اساس سال وکالت#
    contract_date = models.DateField(verbose_name="تاریخ وکالت", null=True, blank=True)
    file = models.FileField(upload_to=upload_to_movakel, verbose_name="فایل موکل", null=True, blank=True)

    def stamp_tax(self):
        return int(self.total_amount * Decimal('0.05'))

    def judiciary_share(self):
        return int(self.total_amount * Decimal('0.05'))

    def annual_tax(self):
        return int(self.total_amount * Decimal('0.25'))

    def total_tax(self):
        return self.stamp_tax() + self.judiciary_share() + self.annual_tax()

    @property
    def contract_year(self):
        """دریافت سال قرارداد"""
        return self.contract_date.year if self.contract_date else "نامشخص"
    
    def get_expert_names(self):
        """دریافت نام و تخصص کارشناسان مرتبط با موکل"""
        return ", ".join([f"{expert.name} ({expert.expertise or 'نامشخص'})" for expert in self.expert.all()])
    def formatted_bail_amount(self):
        """برگرداندن مبلغ وثیقه/کفالت با فرمت عددی"""
        if self.bail_amount:
            return f"{self.bail_amount:,} تومان"
        return "ثبت نشده"

        # متد برای نمایش نوع خدمات
    
    def get_service_type_details(self):
        #if not self.service_type:
            #return "هیچ خدمتی انتخاب نشده است"
        try:
            service = self.service_type
        except ServiceType.DoesNotExist:
            return "هیچ خدمتی انتخاب نشده است"

        services = []
        if self.service_type.defense:
            services.append("دفاع")
        if self.service_type.consultation:
            services.append("مشاوره")
        # ... بقیه فیلدها ...
            
        return "، ".join(services) if services else "هیچ خدمتی انتخاب نشده است"
    
    def get_meeting_date(self):
        """تاریخ ملاقات از درخواست ملاقات مرتبط"""
        if self.request_meeting:
            return self.request_meeting.meeting_date
        return None

    def get_meeting_time(self):
        """زمان ملاقات از درخواست ملاقات مرتبط"""
        if self.request_meeting and hasattr(self.request_meeting, 'start_time'):
            return self.request_meeting.start_time
        return None
    
    def get_archive_numbers(self):
        """دریافت شماره بایگانی‌های مرتبط با پرونده از شعبات"""
        return [archive.archive_no for archive in self.branch_archives.all() if archive.archive_no]

    def add_case_step(self, description):
        step = {
            'date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'description': description
        }
        self.case_steps.append(step)
        self.save()

    def get_case_steps(self):
        return self.case_steps

    """     def add_hearing_schedule(self, date, time):
        hearing_schedule = HearingSchedule(movakel=self, hearing_date=date, hearing_time=time)
        hearing_schedule.save() """

    def get_hearing_dates(self):
        return self.hearing_dates
    
    """     def get_upcoming_hearing(self):
        HearingSchedule = apps.get_model('movakel_module', 'HearingSchedule')  # دریافت مدل به صورت پویا
        return HearingSchedule.objects.filter(
            movakel=self,
            hearing_date__gte=timezone.now().date(),
            is_active=True
        ).order_by('hearing_date').first() """
    
    def get_past_hearings(self):
        """دریافت وقت‌های رسیدگی گذشته"""
        return self.hearing_dates.filter(
            hearing_date__lt=timezone.now().date(),
            is_active=True
        ).order_by('-hearing_date')

    def get_all_hearings(self):
        """دریافت تمام وقت‌های رسیدگی"""
        return self.hearing_dates.filter(is_active=True).order_by('-hearing_date') 

    def get_visits(self):
        """دریافت تمامی مراجعات مرتبط با این موکل"""
        return self.visits.all()
    
    def remaining_amount(self):
        """محاسبه مبلغ باقی‌مانده پرداخت نشده"""
        total_paid = self.installment_payments.filter(is_paid=True).aggregate(Sum('amount'))['amount__sum'] or 0
        return self.total_amount - total_paid

    @property
    def full_name(self):
        """برگرداندن نام کامل موکل بدون جزئیات اضافی"""
        return self.name
    
    def __str__(self):
        archive_nos = ", ".join(self.get_archive_numbers())
        branch_info = ", ".join([
            f"شعبه {archive.branch.name} {archive.branch.category} شماره بایگانی {archive.archive_no}"
            for archive in self.branch_archives.all()
        ])
        


        last_payment = self.movakelpayments.filter(is_delete=False).last()


        if last_payment:
            payment_date = last_payment.payment_date.strftime('%Y-%m-%d')
        else:
            payment_date = "هیچ پرداختی وجود ندارد"

        service_details = self.get_service_type_details()
        expert_count = self.expert.count()

        visits = self.get_visits()
        visits_info = "\n".join([f"تاریخ: {visit.visit_date} | مدت زمان: {visit.visit_duration}" for visit in visits])
        
        # در صورتی که هیچ مراجعه‌ای وجود نداشته باشد، پیامی مناسب نمایش داده می‌شود
        if not visits_info:
            visits_info = "هیچ مراجعه‌ای ثبت نشده است"

        return f"{self.name}"

    def get_absolute_url(self):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
            self.save()
            # اگر slug وجود ندارد، مقدار پیش‌فرض یا دیگری را برگردانید
            #return "/movakels/"
        return reverse('movakel-detail', kwargs={'slug': self.slug})
    
    def delete(self, *args, **kwargs):
        with transaction.atomic():  # برای تضمین یکپارچگی پایگاه داده
        # حذف منطقی پرداخت‌های مرتبط
            self.movakelpayments.all().update(is_delete=True)  
            # حذف منطقی خود پرونده
            self.is_delete = True
            self.save()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)or str(uuid.uuid4())[:10]  # ایجاد اسلاگ از عنوان فارسی              
            # مقدار پیش‌فرض برای service_type اگر None بود
        #if not self.service_type:
            #self.service_type = ServiceType.objects.first()
        super().save(*args, **kwargs)
        
    
    class Meta:
        verbose_name = 'موکل'
        verbose_name_plural = 'موکلین'





class InstallmentPayment(models.Model):
    movakel = models.ForeignKey(Movakel, on_delete=models.CASCADE, related_name='installment_payments', verbose_name='نام موکل')
    amount = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="مبلغ قسط")
    due_date = models.DateField(default=date.today, verbose_name="تاریخ سررسید")
    is_paid = models.BooleanField(default=False, verbose_name="پرداخت شده")
    payment_date = models.DateField(verbose_name='تاریخ پرداخت', null=True, blank=True)

    def status_color(self):
        """تعیین رنگ وضعیت پرداخت"""
        return "green" if self.is_paid else "red"

    def __str__(self):
        status = "✅ پرداخت شده" if self.is_paid else "❌ پرداخت نشده"
        return f"قسط {self.amount} - {status}"

    @property
    def installmentpayment_date_shamsi(self):
        if self.payment_date:
            return jdate.fromgregorian(date=self.payment_date).strftime('%Y/%m/%d')  # تبدیل تاریخ میلادی به شمسی
        return None

    
    class Meta:
        verbose_name = 'قسط پرداختی'
        verbose_name_plural = 'اقساط پرداختی'


class MovakelPayment(ShamsiDateMixin,models.Model):
    movakel = models.ForeignKey(Movakel, on_delete=models.CASCADE, related_name='movakelpayments', verbose_name='پرونده')
    amount = models.DecimalField(max_digits=10, decimal_places=3, verbose_name='مبلغ پرداختی')
    payment_date = models.DateField(verbose_name='تاریخ پرداخت', default=timezone.now)
    payment_method = models.CharField(
        max_length=50,
        choices=PAYMENT_METHOD_CHOICES,
        verbose_name='نحوه پرداخت'
    )
    tracking_number = models.CharField(
        max_length=100,
        verbose_name='شماره پیگیری',
        null=True,
        blank=True
    )
    payment_for = models.CharField(max_length=20, choices=PAYMENT_FOR_CHOICES, verbose_name="بابت هزینه")

    is_delete = models.BooleanField(default=False, verbose_name='حذف شده / نشده')

    def __str__(self):
        # بررسی اینکه آیا payment_date مقداردهی شده است یا خیر
        if self.payment_date:
            return f"مبلغ: {self.amount} - تاریخ: {self.payment_date.strftime('%Y-%m-%d')} - روش: {self.get_payment_method_display()} - {self.get_payment_for_display()}"
        else:
            return f"مبلغ: {self.amount} - روش پرداخت : {self.get_payment_method_display()}"

    class Meta:
        verbose_name = 'پرداخت'
        verbose_name_plural = 'پرداخت‌ها'
        ordering = ['-payment_date']


class PaymentDetail(ShamsiDateMixin,models.Model):
    PAYMENT_TYPES = [
        ('travel_fee', 'هزینه سفر'),                     # travel_fee
        ('miscellaneous_fee', 'هزینه های متفرقه(اوراق ، سی  دیو غیره) '),              # miscellaneous_fee
        ('contract_fee', 'هزینه تنظیم قراردادهای متفرقه'),                   # contract_fee
        ('bill_fee', 'هزینه ارسال لایحه'),                          # bill_fee
        ('initial_fee', 'هزینه دادرسی بدوی (تمبر دادرسی)'),         # initial_fee
        ('appeal_fee', 'هزینه اعتراض (هزینه دادرسی)'),               # appeal_fee
        ('enforcement_fee', 'هزینه اجرای احکام'),                   # enforcement_fee
        ('petition_fee', 'هزینه تنظیم شکواییه'),                    # petition_fee
        ('court_service_fee', 'هزینه دفتر خدمات قضائی'),             # court_service_fee
        ('notification_fee', 'هزینه اخذ ابلاغیه از سامانه'),          # notification_fee
        ('document_fee', 'هزینه اظهارنامه'),                         # document_fee
    ]
    movakel = models.ForeignKey(Movakel, on_delete=models.CASCADE, related_name='payment_details', verbose_name='پرونده')
    payment_type = models.CharField(max_length=50, choices=PAYMENT_TYPES, verbose_name='نوع هزینه')
    amount = models.DecimalField(max_digits=10, decimal_places=3, verbose_name='مقدار هزینه')
    payment_date = models.DateField(verbose_name='تاریخ پرداخت', default=timezone.now, null=True, blank=True)

    def __str__(self):
        return f"{self.get_payment_type_display()} - {self.amount} - {self.payment_date}"

    class Meta:
        verbose_name = 'جزئیات پرداخت'
        verbose_name_plural = 'جزئیات پرداخت‌ها'


class MovakelBranchArchive(models.Model):
    movakel = models.ForeignKey(Movakel, on_delete=models.CASCADE, related_name="branch_archives", verbose_name="پرونده")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="branch_archives", verbose_name="شعبه")
    archive_no = models.CharField(max_length=6, verbose_name="شماره بایگانی", null=True, blank=True)


    def __str__(self):
        return f" شعبه {self.branch.name} - {self.archive_no}"

    class Meta:
        unique_together = ('movakel', 'branch')  # جلوگیری از ثبت شماره بایگانی تکراری برای یک پرونده در یک شعبه


class MovakelGallery(models.Model):
    movakel = models.ForeignKey(Movakel, on_delete=models.CASCADE, verbose_name='پرونده')
    image = models.ImageField(upload_to='images/movakel-gallery', verbose_name='تصویر')

    def __str__(self):
        return self.movakel.name

    class Meta:
        verbose_name = 'تصویر گالری'
        verbose_name_plural = 'گالری تصاویر'



class Visit(models.Model):
    movakel = models.ForeignKey(Movakel, on_delete=models.CASCADE, related_name='visits', verbose_name="موکل")
    visit_date = models.CharField(
        verbose_name="تاریخ مراجعه (شمسی)",
        null=True,
        blank=True,
        max_length=10,

    )  
    start_time = models.TimeField(
        verbose_name="زمان ورود", 
        null=True, 
        blank=True,
        default=None
    )
    end_time = models.TimeField(
        verbose_name="زمان خروج", 
        null=True, 
        blank=True,
        default=None
    )
    visit_duration = models.CharField(max_length=50, blank=True, null=True, verbose_name="مدت جلسه (دقیقه)")
    description = models.TextField(verbose_name="توضیحات", null=True, blank=True)



    def get_gregorian_date(self):
        """تبدیل تاریخ شمسی به میلادی برای محاسبات"""
        if self.visit_date:
            try:
                year, month, day = map(int, self.visit_date.split('-'))
                return jdatetime.date(year, month, day).togregorian()
            except:
                return None
        return None

    def get_jalali_date(self):
        if self.visit_date:
            try:
                jalali_date = jdatetime.date.fromgregorian(date=self.visit_date)
                return f"{jalali_date.year}/{jalali_date.month:02d}/{jalali_date.day:02d}"
            except:
                return "تاریخ نامعتبر"
        return "---"
    
    @property
    def visit_date_shamsi(self):
        if self.visit_date:
            try:
                return jdatetime.date.fromgregorian(date=self.visit_date).strftime('%Y/%m/%d')
            except:
                return "تاریخ نامعتبر"
        return None

    def calculate_duration(self):
        if self.start_time and self.end_time:
            start_dt = datetime.datetime.combine(datetime.date.today(), self.start_time)
            end_dt = datetime.datetime.combine(datetime.date.today(), self.end_time)
            duration = end_dt - start_dt
            duration_minutes = int(duration.total_seconds() // 60)
            return f"{duration_minutes} دقیقه"
        return None

    def save(self, *args, **kwargs):
        self.visit_duration = self.calculate_duration()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"مراجعه به (مدت: {self.visit_duration or 'ثبت نشده'})"

    class Meta:
        verbose_name = 'مراجعه'
        verbose_name_plural = 'مراجعات'

