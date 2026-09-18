from datetime import timedelta, date, datetime, time
from decimal import Decimal
import os
import uuid

from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone
from django.db.models import Sum
from django.core.validators import RegexValidator
from django.apps import apps

from django_jalali.db import models as jmodels
import jdatetime
from jdatetime import date as jdate
from jalali_date import date2jalali, datetime2jalali
from slugify import slugify  # python-slugify — پشتیبانی از فارسی

from account_module.models import User


# ============================================================
# Choices
# ============================================================
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

ZERO = Decimal('0')


def _d(value):
    """تبدیل ایمن هر مقدار عددی به Decimal"""
    if value is None:
        return ZERO
    return Decimal(str(value))


def upload_to_movakel(instance, filename):
    """بر اساس سال وکالت مسیر ذخیره فایل را مشخص می‌کند"""
    year = instance.contract_date.year if instance.contract_date else timezone.now().year
    return os.path.join(f'movakels/{year}/', filename)


# ============================================================
# Mixin
# ============================================================
class ShamsiDateMixin(models.Model):
    """Abstract mixin برای نمایش تاریخ شمسی"""
    class Meta:
        abstract = True

    @property
    def shamsi_date(self):
        if hasattr(self, 'date') and isinstance(self.date, (date, datetime)):
            return jdatetime.date.fromgregorian(date=self.date).strftime('%Y/%m/%d')
        if hasattr(self, 'meeting_date') and isinstance(self.meeting_date, (date, datetime)):
            return jdatetime.date.fromgregorian(date=self.meeting_date).strftime('%Y/%m/%d')
        return "-"


# ============================================================
# Manager
# ============================================================
class MovakelManager(models.Manager):
    """فقط رکوردهای حذف‌نشده را برمی‌گرداند"""
    def get_queryset(self):
        return super().get_queryset().filter(is_delete=False)


# ============================================================
# Models
# ============================================================
class MovakelCategory(models.Model):
    title = models.CharField(max_length=300, db_index=True, verbose_name='عنوان')
    url_title = models.CharField(max_length=300, db_index=True,
                                 verbose_name='عنوان در url', blank=True, null=True)

    def save(self, *args, **kwargs):
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
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'فایل pdf'
        verbose_name_plural = 'فایل های pdf'


class Branch(models.Model):
    name = models.CharField(max_length=255, verbose_name="نام شعبه")
    category = models.CharField(max_length=255, verbose_name="نوع دسته‌بندی")

    def __str__(self):
        return f"شعبه {self.name} {self.category}"

    class Meta:
        verbose_name = 'شعبه'
        verbose_name_plural = 'شعبات'


class ServiceType(models.Model):
    movakel = models.OneToOneField('Movakel', on_delete=models.CASCADE,
                                   related_name='service_type')
    office_study = models.BooleanField(default=False, blank=True, verbose_name="مطالعه پرونده")
    defense = models.BooleanField(default=False, blank=True, verbose_name='دفاع')
    consultation = models.BooleanField(default=False, blank=True, verbose_name='مشاوره')
    check_documents = models.BooleanField(default=False, blank=True, verbose_name='بررسی مدارک')
    contract = models.BooleanField(default=False, blank=True, verbose_name='تنظیم قراردادهای متفرقه')
    notification = models.BooleanField(default=False, blank=True, verbose_name="اخذ ابلاغیه")
    bill = models.BooleanField(default=False, blank=True, verbose_name='لایحه')

    # هزینه‌های مربوط به اختیار وکیل
    travel_fee = models.DecimalField(max_digits=12, decimal_places=0, default=0,
                                     verbose_name="هزینه سفر (هتل، وسیله نقلیه و غیره)")
    miscellaneous_fee = models.DecimalField(max_digits=12, decimal_places=0, default=0,
                                            verbose_name="هزینه‌های متفرقه")
    office_study_fee = models.DecimalField(max_digits=12, decimal_places=0, default=0,
                                           verbose_name="هزینه مطالعه پرونده")
    contract_fee = models.DecimalField(max_digits=12, decimal_places=0, default=0,
                                       verbose_name="هزینه تنظیم قراردادهای متفرقه")

    # هزینه کلی برای خدمات وکیل
    lawyer_services_fee = models.DecimalField(max_digits=12, decimal_places=0, default=0,
                                              verbose_name='هزینه کل خدمات وکیل')

    # فیلدهای مربوط به هزینه دادرسی
    bill_fee = models.DecimalField(max_digits=12, decimal_places=0, default=0,
                                   verbose_name="هزینه ارسال لوایح")
    initial_fee = models.DecimalField(max_digits=12, decimal_places=0, default=0,
                                      verbose_name="هزینه دادرسی بدوی (تمبر دادرسی)")
    appeal_fee = models.DecimalField(max_digits=12, decimal_places=0, default=0,
                                     verbose_name="هزینه اعتراض (هزینه دادرسی)")
    enforcement_fee = models.DecimalField(max_digits=12, decimal_places=0, default=0,
                                          verbose_name="هزینه اجرای احکام")
    petition_fee = models.DecimalField(max_digits=12, decimal_places=0, default=0,
                                       verbose_name="هزینه تنظیم شکوائیه")
    court_service_fee = models.DecimalField(max_digits=12, decimal_places=0, default=0,
                                            verbose_name="هزینه دفتر خدمات قضائی")
    document_fee = models.DecimalField(max_digits=12, decimal_places=0, default=0,
                                       verbose_name="هزینه اظهارنامه")
    notification_fee = models.DecimalField(max_digits=12, decimal_places=0, default=0,
                                           verbose_name="هزینه اخذ ابلاغیه از سامانه")

    def get_selected_services(self):
        """برگرداندن لیست خدمات انتخاب شده"""
        mapping = [
            ('defense', 'دفاع'),
            ('consultation', 'مشاوره'),
            ('check_documents', 'بررسی مدارک'),
            ('office_study', 'مطالعه پرونده'),
            ('contract', 'تنظیم قراردادهای متفرقه'),
            ('notification', 'اخذ ابلاغیه'),
            ('bill', 'لایحه'),
        ]
        return [label for field, label in mapping if getattr(self, field)]

    @property
    def total_fee(self):
        """جمع کل هزینه‌ها (خدمات + دادرسی)"""
        return sum([
            _d(self.lawyer_services_fee),
            _d(self.bill_fee),
            _d(self.initial_fee),
            _d(self.appeal_fee),
            _d(self.enforcement_fee),
            _d(self.petition_fee),
            _d(self.court_service_fee),
            _d(self.document_fee),
        ], ZERO)

    def total_litigation_fees(self):
        """جمع کل هزینه‌های دادرسی"""
        return sum([
            _d(self.bill_fee),
            _d(self.initial_fee),
            _d(self.appeal_fee),
            _d(self.enforcement_fee),
            _d(self.petition_fee),
            _d(self.court_service_fee),
            _d(self.document_fee),
        ], ZERO)

    def __str__(self):
        return str(self.movakel)

    class Meta:
        verbose_name = 'اقدام'
        verbose_name_plural = 'اقدامات'


class DefenseDocument(ShamsiDateMixin, models.Model):
    STAGE_CHOICES = [
        ('initial', 'بدوی'),
        ('appeal', 'تجدیدنظر'),
        ('execution', 'اجرای احکام'),
        ('petition', 'تنظیم لایحه'),
    ]

    movakel = models.ForeignKey('Movakel', on_delete=models.CASCADE,
                                related_name='defense_documents', verbose_name='موکل')
    stage = models.CharField(max_length=500, choices=STAGE_CHOICES, verbose_name="مرحله")
    subject = models.CharField(max_length=255, verbose_name="موضوع")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")
    pdf_file = models.FileField(upload_to='documents/pdf/', null=True, blank=True,
                                verbose_name="فایل PDF")
    word_file = models.FileField(upload_to='documents/word/', null=True, blank=True,
                                 verbose_name="فایل Word")
    slug = models.CharField(max_length=255, unique=True, blank=True, null=True,
                            verbose_name='اسلاگ')

    @property
    def mechanized_number(self):
        return self.movakel.mechanized_number if self.movakel else None

    def __str__(self):
        return f"{self.movakel.name} - {self.get_stage_display()}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = f"{self.movakel.name}-{self.get_stage_display()}".replace(" ", "-")
            slug = base
            counter = 1
            max_attempts = 100
            while DefenseDocument.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                if counter > max_attempts:
                    slug = f"{base}-{uuid.uuid4().hex[:8]}"
                    break
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_jalali_date(self):
        return datetime2jalali(self.created_at).strftime('%Y/%m/%d')

    class Meta:
        verbose_name = 'تنظیم لایحه'
        verbose_name_plural = 'تنظیم لایحه ها'


class MeetingSubject(models.Model):
    name = models.CharField(max_length=100, verbose_name="عنوان موضوع")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "موضوع ملاقات"
        verbose_name_plural = "موضوعات ملاقات"


class RequestMeeting(ShamsiDateMixin, models.Model):
    MEETING_TYPES = [
        ('phone', 'تلفنی'),
        ('in_person', 'حضوری'),
        ('online', 'آنلاین'),
    ]
    STATUS_CHOICES = [
        ('pending', 'مشاوره'),
        ('converted', 'موکل'),
    ]

    status = models.CharField(max_length=10, choices=STATUS_CHOICES,
                              default='pending', verbose_name="وضعیت درخواست")
    movakel = models.ForeignKey('Movakel', on_delete=models.CASCADE,
                                related_name='meetings', null=True, blank=True)
    full_name = models.CharField(max_length=255, verbose_name="نام و نام خانوادگی")
    national_id = models.CharField(max_length=10, verbose_name="کد ملی", db_index=True)
    identification_number = models.CharField(max_length=20, verbose_name="شماره شناسنامه",
                                             blank=True, null=True)
    birth_date = models.DateField(verbose_name="تاریخ تولد", blank=True, null=True)
    phone_number = models.CharField(max_length=11, verbose_name="تلفن ثابت",
                                    blank=True, null=True)
    mobile_number = models.CharField(max_length=11, verbose_name="تلفن همراه")
    virtual_number = models.CharField(
        max_length=11, verbose_name="شماره فضای مجازی", blank=True, null=True,
        validators=[RegexValidator(regex=r'^\d{1,11}$',
                                   message="شماره باید فقط شامل اعداد و حداکثر ۱۱ رقم باشد.")]
    )
    email = models.EmailField(verbose_name="نشانی اینترنتی", blank=True, null=True)
    address = models.TextField(verbose_name="آدرس", blank=True, null=True)
    postal_code = models.CharField(max_length=10, verbose_name="کدپستی", blank=True, null=True)
    meeting_type = models.CharField(max_length=20, choices=MEETING_TYPES, verbose_name="نوع ملاقات")
    meeting_subject = models.ManyToManyField('MeetingSubject', verbose_name="موضوع ملاقات", blank=True)
    start_time = models.TimeField(verbose_name="زمان ورود", null=True, blank=True)
    end_time = models.TimeField(verbose_name="زمان خروج", null=True, blank=True)
    meeting_date = models.DateTimeField(verbose_name="تاریخ ملاقات", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان درخواست")
    meeting_fee = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True,
                                      default=0, verbose_name="هزینه ملاقات")
    duration = models.CharField(max_length=50, blank=True, null=True, verbose_name="مدت جلسه")
    related_movakel = models.ForeignKey(
        'Movakel', on_delete=models.SET_NULL, null=True, blank=True,
        related_name="related_request_meetings",
        verbose_name="وکالت داده شده (سابقه مراجعه)"
    )

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
            return self.meeting_date.strftime('%Y-%m-%d %H:%M:%S')
        return "-"
    meeting_date_formatted.short_description = "تاریخ ملاقات"


    def save(self, *args, **kwargs):
        if self.start_time and self.end_time:
            today = date.today()
            start = datetime.combine(today, self.start_time)
            end = datetime.combine(today, self.end_time)
            diff = int((end - start).total_seconds() // 60)
            self.duration = f"{diff} دقیقه" if diff > 0 else "کمتر از ۱ دقیقه"

        if self.status == 'converted' and not self.related_movakel:
            slug_base = slugify(self.full_name, allow_unicode=True) or str(uuid.uuid4())[:10]
            slug = slug_base
            counter = 1
            max_attempts = 100
            while Movakel.all_objects.filter(slug=slug).exists():
                if counter > max_attempts:
                    slug = f"{slug_base}-{uuid.uuid4().hex[:8]}"
                    break
                slug = f"{slug_base}-{counter}"
                counter += 1

            self.related_movakel = Movakel.all_objects.create(
                name=self.full_name,
                mobile_number=self.mobile_number,
                file_number=self.phone_number or '',
                mechanized_number=str(uuid.uuid4())[:10],
                national_id=self.national_id or '',
                description=f"پرونده مربوط به {self.full_name}",
                age="0",
                is_active=True,
                slug=slug,
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return self.full_name

    class Meta:
        verbose_name = "درخواست ملاقات"
        verbose_name_plural = "درخواست‌های ملاقات"


class Expert(models.Model):
    name = models.CharField(max_length=300, verbose_name='نام کارشناس')
    mobile_number = models.CharField(max_length=11, verbose_name='شماره همراه', null=True, blank=True)
    expertise = models.CharField(max_length=255, verbose_name="تخصص", default="نامشخص")

    def __str__(self):
        return f"{self.name} - {self.expertise}"

    class Meta:
        verbose_name = 'کارشناس'
        verbose_name_plural = 'کارشناسان'



class MovakelType(models.Model):
    title = models.CharField(max_length=200, verbose_name='عنوان')
    url_title = models.CharField(max_length=200, blank=True, null=True,
                                 verbose_name='عنوان در URL')

    def save(self, *args, **kwargs):
        if not self.url_title:
            self.url_title = slugify(self.title, allow_unicode=True).replace('_', '-')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'نوع پرونده'
        verbose_name_plural = 'انواع پرونده'

class Movakel(ShamsiDateMixin, models.Model):
    CASE_STATUS_CHOICES = [
        ('in_progress', 'در جریان'),
        ('appeal', 'تجدیدنظر'),
        ('execution', 'اجرای حکم'),
        ('closed', 'مختومه'),
        ('archived', 'بایگانی'),
    ]

    request_meeting = models.ForeignKey(RequestMeeting, on_delete=models.CASCADE,
                                        verbose_name="درخواست ملاقات",
                                        related_name="movakels", null=True, blank=True)
    name = models.CharField(max_length=300, verbose_name='نام موکل')
    national_id = models.CharField(max_length=10, verbose_name='کد ملی', blank=True, db_index=True)

    branchs = models.ManyToManyField(Branch, blank=True)
    category = models.ForeignKey(MovakelCategory, on_delete=models.SET_NULL,
                                 related_name='movakel_categories', null=True, blank=True,
                                 verbose_name='دسته‌بندی‌ها')
    type = models.ForeignKey(       
        MovakelType,
        on_delete=models.SET_NULL,
        related_name='movakels',
        null=True, blank=True,
        verbose_name='نوع پرونده'
    )
    image = models.ImageField(upload_to='images/movakels', null=True, blank=True,
                              verbose_name='تصویر پرونده')
    pdf_files = models.ManyToManyField(PDFFile, blank=True, related_name="movakels",
                                       verbose_name="فایل‌های PDF")
    defensedocument_set = models.ManyToManyField(DefenseDocument, blank=True,
                                                 related_name="movakels")
    presenter = models.CharField(max_length=300, null=True, verbose_name='معرف')
    age = models.CharField(max_length=3, verbose_name='سن')
    mobile_number = models.CharField(max_length=11, verbose_name='شماره همراه')
    file_number = models.CharField(max_length=11, null=True, verbose_name='شماره تلفن ثابت')
    mechanized_number = models.CharField(null=True, max_length=20, verbose_name='شماره مکانیزه')
    description = models.TextField(verbose_name='توضیحات اصلی', db_index=True)
    slug = models.SlugField(unique=True, blank=True, allow_unicode=True)

    is_active = models.BooleanField(default=False, verbose_name='فعال / غیرفعال')
    is_delete = models.BooleanField(default=False, verbose_name='حذف شده / نشده')

    case_status = models.CharField(max_length=20, choices=CASE_STATUS_CHOICES,
                                   default='in_progress', verbose_name='وضعیت پرونده')

    objects = MovakelManager()
    all_objects = models.Manager()

    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES,
                                      verbose_name='نحوه پرداخت', null=True, blank=True)
    final_result = models.TextField(null=True, blank=True, verbose_name="ملاحظات")
    case_steps = models.JSONField(default=list, blank=True, verbose_name="مراحل پرونده")

    hearing_date = models.DateField(null=True, blank=True, verbose_name="وقت رسیدگی / وقت نظارت")
    hearing_time = models.TimeField(null=True, blank=True, verbose_name="زمان رسیدگی")

    primary_archive_no = models.CharField(max_length=6, null=True, blank=True,
                                          verbose_name="شماره بایگانی بدوی")
    primary_court_number = models.CharField(max_length=20, null=True, blank=True,
                                            verbose_name="شماره دادنامه بدوی")
    primary_court_notification_date = models.DateField(null=True, blank=True,
                                                       verbose_name="تاریخ ابلاغ بدوی")
    primary_court_result = models.TextField(null=True, blank=True, verbose_name="نتیجه رأی بدوی")

    appeal_archive_no = models.CharField(max_length=6, null=True, blank=True,
                                         verbose_name="شماره بایگانی تجدیدنظر")
    appeal_court_number = models.CharField(max_length=20, null=True, blank=True,
                                           verbose_name="شماره دادنامه تجدیدنظر")
    appeal_court_notification_date = models.DateField(null=True, blank=True,
                                                      verbose_name="تاریخ ابلاغ تجدیدنظر")
    appeal_court_result = models.TextField(null=True, blank=True, verbose_name="نتیجه رأی تجدیدنظر")

    executive_archive_no = models.CharField(max_length=6, null=True, blank=True,
                                            verbose_name="شماره بایگانی اجرای احکام")
    executive_court_result = models.TextField(null=True, blank=True, verbose_name="عملیات اجرائی")
    executive_case_number = models.CharField(max_length=6, null=True, blank=True,
                                             verbose_name="شماره اجرائیه پرونده")
    executive_case_notification_date = models.DateField(null=True, blank=True,
                                                        verbose_name="تاریخ ابلاغ اجرائیه پرونده")
    auction_date = models.DateField(null=True, blank=True, verbose_name="تاریخ مزایده")

    total_amount = models.PositiveIntegerField(verbose_name="مبلغ کل حق الوکاله", default=0)
    bail_amount = models.PositiveIntegerField(null=True, blank=True,
                                              verbose_name="مبلغ وثیقه/کفالت (تومان)")

    primary_branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name="primary_movakels", verbose_name="شعبه بدوی")
    appeal_branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name="appeal_movakels", verbose_name="شعبه تجدیدنظر")
    executive_branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name='executive_branches',
                                         verbose_name="شعبه اجرای احکام")

    expert = models.ManyToManyField(Expert, blank=True, related_name="movakels",
                                    verbose_name="کارشناس")

    contract_date = models.DateField(verbose_name="تاریخ وکالت", null=True, blank=True)
    file = models.FileField(upload_to=upload_to_movakel, verbose_name="فایل موکل",
                            null=True, blank=True)

    # --------------------------------------------------------
    # مالیات‌ها (Decimal-safe)
    # --------------------------------------------------------
    def stamp_tax(self):
        return int(_d(self.total_amount) * Decimal('0.05'))

    def judiciary_share(self):
        return int(_d(self.total_amount) * Decimal('0.05'))

    def annual_tax(self):
        return int(_d(self.total_amount) * Decimal('0.25'))

    def total_tax(self):
        return self.stamp_tax() + self.judiciary_share() + self.annual_tax()

    @property
    def contract_year(self):
        return self.contract_date.year if self.contract_date else "نامشخص"

    @property
    def full_name(self):
        return self.name

    # --------------------------------------------------------
    # خواص مشتق‌شده از ServiceType
    # --------------------------------------------------------
    @property
    def lawyer_services_fee(self):
        try:
            return self.service_type.lawyer_services_fee
        except (ServiceType.DoesNotExist, AttributeError):
            return 0

    @property
    def total_litigation_fees(self):
        try:
            return self.service_type.total_litigation_fees()
        except (ServiceType.DoesNotExist, AttributeError):
            return 0

    def get_expert_names(self):
        return ", ".join(
            f"{expert.name} ({expert.expertise or 'نامشخص'})"
            for expert in self.expert.all()
        )

    def formatted_bail_amount(self):
        if self.bail_amount:
            return f"{self.bail_amount:,} تومان"
        return "ثبت نشده"

    def get_service_type_details(self):
        try:
            service = self.service_type
        except ServiceType.DoesNotExist:
            return "هیچ خدمتی انتخاب نشده است"

        selected = service.get_selected_services()
        return "، ".join(selected) if selected else "هیچ خدمتی انتخاب نشده است"

    def get_meeting_date(self):
        return self.request_meeting.meeting_date if self.request_meeting else None

    def get_meeting_time(self):
        if self.request_meeting and hasattr(self.request_meeting, 'start_time'):
            return self.request_meeting.start_time
        return None

    def get_archive_numbers(self):
        return [a.archive_no for a in self.branch_archives.all() if a.archive_no]

    def add_case_step(self, description):
        step = {
            'date': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'description': description
        }
        self.case_steps.append(step)
        self.save(update_fields=['case_steps'])

    def get_case_steps(self):
        return self.case_steps

    def get_visits(self):
        return self.visits.all()

    def remaining_amount(self):
        """محاسبه مبلغ باقی‌مانده پرداخت نشده (بر اساس اقساط پرداخت‌شده)"""
        total_paid = (
            self.installment_payments.filter(is_paid=True)
            .aggregate(Sum('amount'))['amount__sum'] or 0
        )
        return self.total_amount - total_paid

    def get_absolute_url(self):
        if not self.slug:
            self.save()  # save() خودش slug رو می‌سازه
        return reverse('movakel-detail', kwargs={'slug': self.slug})

    # --------------------------------------------------------
    # Soft Delete
    # --------------------------------------------------------
    def delete(self, *args, **kwargs):
        with transaction.atomic():
            MovakelPayment.objects.filter(movakel=self).update(is_delete=True)
            Movakel.all_objects.filter(pk=self.pk).update(is_delete=True)
            self.is_delete = True
        return 0, {}  # soft delete: هیچ رکوردی از DB حذف نشد

    # --------------------------------------------------------
    # Save — با slug یکتا
    # --------------------------------------------------------
    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name, allow_unicode=True) or str(uuid.uuid4())[:10]
            slug = base
            counter = 1
            max_attempts = 100
            while Movakel.all_objects.filter(slug=slug).exclude(pk=self.pk).exists():
                if counter > max_attempts:
                    # اگر بعد از ۱۰۰ تلاش هم اسلاگ یکتا پیدا نشد (بسیار بعید)،
                    # با یک پسوند تصادفی تضمین‌شده یکتا، از حلقهٔ بی‌پایان خارج می‌شویم.
                    slug = f"{base}-{uuid.uuid4().hex[:8]}"
                    break
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'موکل'
        verbose_name_plural = 'موکلین'


class InstallmentPayment(models.Model):
    movakel = models.ForeignKey(Movakel, on_delete=models.CASCADE,
                                related_name='installment_payments', verbose_name='نام موکل')
    amount = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="مبلغ قسط")
    due_date = models.DateField(default=date.today, verbose_name="تاریخ سررسید")
    is_paid = models.BooleanField(default=False, verbose_name="پرداخت شده")
    payment_date = models.DateField(verbose_name='تاریخ پرداخت', null=True, blank=True)

    def status_color(self):
        return "green" if self.is_paid else "red"

    def __str__(self):
        status = "✅ پرداخت شده" if self.is_paid else "❌ پرداخت نشده"
        return f"قسط {self.amount} - {status}"

    @property
    def installmentpayment_date_shamsi(self):
        if self.payment_date:
            return jdate.fromgregorian(date=self.payment_date).strftime('%Y/%m/%d')
        return None

    class Meta:
        verbose_name = 'قسط پرداختی'
        verbose_name_plural = 'اقساط پرداختی'


class MovakelPayment(ShamsiDateMixin, models.Model):
    movakel = models.ForeignKey(Movakel, on_delete=models.CASCADE,
                                related_name='movakelpayments', verbose_name='پرونده')
    amount = models.DecimalField(max_digits=12, decimal_places=0, verbose_name='مبلغ پرداختی')
    payment_date = models.DateField(verbose_name='تاریخ پرداخت', default=timezone.now)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES,
                                      verbose_name='نحوه پرداخت')
    tracking_number = models.CharField(max_length=100, verbose_name='شماره پیگیری',
                                       null=True, blank=True)
    payment_for = models.CharField(max_length=20, choices=PAYMENT_FOR_CHOICES,
                                   verbose_name="بابت هزینه")
    is_delete = models.BooleanField(default=False, verbose_name='حذف شده / نشده')

    def __str__(self):
        if self.payment_date:
            return (f"مبلغ: {self.amount} - تاریخ: {self.payment_date.strftime('%Y-%m-%d')} "
                    f"- روش: {self.get_payment_method_display()} "
                    f"- {self.get_payment_for_display()}")
        return f"مبلغ: {self.amount} - روش پرداخت: {self.get_payment_method_display()}"

    class Meta:
        verbose_name = 'پرداخت'
        verbose_name_plural = 'پرداخت‌ها'
        ordering = ['-payment_date']


class PaymentDetail(ShamsiDateMixin, models.Model):
    PAYMENT_TYPES = [
        ('travel_fee', 'هزینه سفر'),
        ('miscellaneous_fee', 'هزینه‌های متفرقه'),
        ('contract_fee', 'هزینه تنظیم قراردادهای متفرقه'),
        ('bill_fee', 'هزینه ارسال لایحه'),
        ('initial_fee', 'هزینه دادرسی بدوی (تمبر دادرسی)'),
        ('appeal_fee', 'هزینه اعتراض (هزینه دادرسی)'),
        ('enforcement_fee', 'هزینه اجرای احکام'),
        ('petition_fee', 'هزینه تنظیم شکواییه'),
        ('court_service_fee', 'هزینه دفتر خدمات قضائی'),
        ('notification_fee', 'هزینه اخذ ابلاغیه از سامانه'),
        ('document_fee', 'هزینه اظهارنامه'),
    ]
    movakel = models.ForeignKey(Movakel, on_delete=models.CASCADE,
                                related_name='payment_details', verbose_name='پرونده')
    payment_type = models.CharField(max_length=50, choices=PAYMENT_TYPES, verbose_name='نوع هزینه')
    amount = models.DecimalField(max_digits=12, decimal_places=0, verbose_name='مقدار هزینه')
    payment_date = models.DateField(verbose_name='تاریخ پرداخت',
                                    default=timezone.now, null=True, blank=True)

    def __str__(self):
        return f"{self.get_payment_type_display()} - {self.amount} - {self.payment_date}"

    class Meta:
        verbose_name = 'جزئیات پرداخت'
        verbose_name_plural = 'جزئیات پرداخت‌ها'


class MovakelBranchArchive(models.Model):
    movakel = models.ForeignKey(Movakel, on_delete=models.CASCADE,
                                related_name="branch_archives", verbose_name="پرونده")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE,
                               related_name="branch_archives", verbose_name="شعبه")
    archive_no = models.CharField(max_length=6, verbose_name="شماره بایگانی", null=True, blank=True)

    def __str__(self):
        return f"شعبه {self.branch.name} - {self.archive_no}"

    class Meta:
        unique_together = ('movakel', 'branch')
        indexes = [
            models.Index(fields=['movakel', 'branch']),
        ]


class MovakelGallery(models.Model):
    movakel = models.ForeignKey(Movakel, on_delete=models.CASCADE, verbose_name='پرونده')
    image = models.ImageField(upload_to='images/movakel-gallery', verbose_name='تصویر')

    def __str__(self):
        return self.movakel.name

    class Meta:
        verbose_name = 'تصویر گالری'
        verbose_name_plural = 'گالری تصاویر'


class Visit(models.Model):
    movakel = models.ForeignKey(Movakel, on_delete=models.CASCADE,
                                related_name='visits', verbose_name="موکل")
    visit_date = jmodels.jDateField(
        verbose_name="تاریخ مراجعه (شمسی)", null=True, blank=True
    )
    start_time = models.TimeField(verbose_name="زمان ورود", null=True, blank=True, default=None)
    end_time = models.TimeField(verbose_name="زمان خروج", null=True, blank=True, default=None)
    visit_duration = models.CharField(max_length=50, blank=True, null=True,
                                      verbose_name="مدت جلسه (دقیقه)")
    description = models.TextField(verbose_name="توضیحات", null=True, blank=True)

    @property
    def visit_date_shamsi(self):
        if self.visit_date:
            try:
                return jdatetime.date.fromgregorian(date=self.visit_date).strftime('%Y/%m/%d')
            except Exception:
                return "تاریخ نامعتبر"
        return None

    def calculate_duration(self):
        if self.start_time and self.end_time:
            start_dt = datetime.combine(date.today(), self.start_time)
            end_dt = datetime.combine(date.today(), self.end_time)
            minutes = int((end_dt - start_dt).total_seconds() // 60)
            if minutes > 0:
                return f"{minutes} دقیقه"
            return "کمتر از ۱ دقیقه"
        return None

    def save(self, *args, **kwargs):
        self.visit_duration = self.calculate_duration()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"مراجعه {self.movakel.name} (مدت: {self.visit_duration or 'ثبت نشده'})"

    class Meta:
        verbose_name = 'مراجعه'
        verbose_name_plural = 'مراجعات'
        
        
        
