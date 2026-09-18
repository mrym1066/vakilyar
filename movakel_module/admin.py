from decimal import Decimal
import jdatetime
from jdatetime import date as jdate

from django import forms
from django.contrib import admin
from django.db import transaction
from django.db.models import Sum
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import MovakelType

from jalali_date.admin import ModelAdminJalaliMixin
from jalali_date.widgets import AdminJalaliDateWidget
from jalali_date import datetime2jalali

from . import models
from .models import (
    Movakel, Expert, InstallmentPayment, MeetingSubject, Visit,
    ServiceType, DefenseDocument, PDFFile, Branch, MovakelBranchArchive,
    RequestMeeting, MovakelCategory, MovakelGallery, MovakelPayment,
    PaymentDetail,
)


# ============================================================
# اعداد فارسی
# ============================================================
PERSIAN_DIGITS = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')


def format_ir_number(number):
    if number is None:
        return "۰"
    try:
        d = Decimal(str(number))
    except Exception:
        return "۰"

    is_negative = d < 0
    d = abs(d)
    integer_part = int(d)
    decimal_part = d - integer_part

    formatted = "{:,}".format(integer_part)
    if decimal_part > 0:
        decimal_str = str(decimal_part).split('.')[1].rstrip('0')
        if decimal_str:
            formatted = f"{formatted}.{decimal_str}"

    formatted = formatted.translate(PERSIAN_DIGITS)
    return f"-{formatted}" if is_negative else formatted

def format_toman(number):
    return f"{format_ir_number(number)} تومان"


# ============================================================
# Forms
# ============================================================
class MovakelAdminForm(forms.ModelForm):
    """فرم ادمین موکل (import از این فایل)"""
    class Meta:
        model = Movakel
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        total_amount = cleaned_data.get('total_amount') or 0
        if total_amount < 0:
            raise forms.ValidationError("مبلغ کل حق‌الوکاله نمی‌تواند منفی باشد.")
        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['final_result'].widget = forms.Textarea(attrs={'rows': 4, 'cols': 50})


# ============================================================
# Inlines
# ============================================================
class PDFFileInline(admin.StackedInline):
    model = Movakel.pdf_files.through
    extra = 0


class MovakelBranchArchiveInline(admin.TabularInline):
    model = MovakelBranchArchive
    extra = 0
    verbose_name = "شعبه"
    verbose_name_plural = "شعبه‌ها"


class DefenseDocumentInline(admin.TabularInline):
    model = DefenseDocument
    extra = 0
    verbose_name = 'مدرک دفاعی'
    verbose_name_plural = 'مدارک دفاعی'
    fields = ('stage', 'subject', 'pdf_file', 'word_file')


class ExpertInline(admin.TabularInline):
    model = Movakel.expert.through
    extra = 0
    verbose_name = 'کارشناس'
    verbose_name_plural = 'کارشناسان'
    fields = ('expert',)


class InstallmentPaymentInline(admin.TabularInline):
    model = InstallmentPayment
    extra = 0
    verbose_name = 'پرداخت حق الوکاله'
    verbose_name_plural = 'پرداخت‌های حق الوکاله'
    fields = ('amount', 'due_date', 'is_paid', 'payment_date')


# ============================================================
# Admins
# ============================================================
class BranchAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = ('name', 'category')
    search_fields = ('name', 'category')


@admin.register(DefenseDocument)
class DefenseDocumentAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = ['stage', 'movakel']
    search_fields = ['movakel__name']
    list_filter = ['stage']


@admin.register(PDFFile)
class PDFFileAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = ['name', 'file', 'uploaded_at']


# ------------------------------------------------------------
# ServiceType
# ------------------------------------------------------------
class ServiceTypeAdminForm(forms.ModelForm):
    class Meta:
        model = ServiceType
        fields = '__all__'
        widgets = {
            'defense': forms.CheckboxInput(attrs={'class': 'inline-checkbox'}),
            'consultation': forms.CheckboxInput(attrs={'class': 'inline-checkbox'}),
            'check_documents': forms.CheckboxInput(attrs={'class': 'inline-checkbox'}),
            'office_study': forms.CheckboxInput(attrs={'class': 'inline-checkbox'}),
            'contract': forms.CheckboxInput(attrs={'class': 'inline-checkbox'}),
            'bill': forms.CheckboxInput(attrs={'class': 'inline-checkbox'}),
            'notification': forms.CheckboxInput(attrs={'class': 'inline-checkbox'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False


@admin.register(ServiceType)
class ServiceTypeAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    form = ServiceTypeAdminForm
    search_fields = ('movakel__name',)

    fieldsets = (
        ('موکل', {'fields': ('movakel',)}),
        ('اختیار وکیل', {
            'fields': ('office_study', 'defense', 'consultation', 'check_documents',
                       'contract', 'notification', 'bill', 'lawyer_services_fee')
        }),
        ('هزینه دادرسی', {
            'fields': ('bill_fee', 'initial_fee', 'appeal_fee', 'enforcement_fee',
                       'petition_fee', 'travel_fee', 'miscellaneous_fee', 'contract_fee',
                       'notification_fee', 'court_service_fee', 'document_fee',
                       'total_litigation_fees_display',)
        }),
    )

    list_display = (
        'movakel', 'defense', 'consultation', 'check_documents', 'contract',
        'office_study', 'bill', 'lawyer_services_fee_display',
        'total_litigation_fees_display',
    )
    list_filter = ('defense', 'consultation', 'check_documents', 'contract', 'bill')
    list_editable = ('defense', 'office_study', 'consultation', 'check_documents', 'contract', 'bill')
    readonly_fields = ('total_litigation_fees_display',)

    @admin.display(description="هزینه کل خدمات وکیل")
    def lawyer_services_fee_display(self, obj):
        return format_toman(obj.lawyer_services_fee)

    @admin.display(description='جمع کل هزینه دادرسی')
    def total_litigation_fees_display(self, obj):
        return format_toman(obj.total_litigation_fees())

    class Media:
        css = {'all': ('admin/css/custom_admin.css',)}


# ------------------------------------------------------------
# RequestMeeting
# ------------------------------------------------------------
@admin.register(RequestMeeting)
class RequestMeetingAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = ['full_name', 'national_id', 'meeting_date_formatted',
                    'start_time', 'end_time', 'duration', 'meeting_date']
    list_filter = ('meeting_type', 'created_at')
    search_fields = ('full_name', 'national_id')
    ordering = ('-created_at',)
    filter_horizontal = ('meeting_subject',)
    jalali_date_fields = ('meeting_date',)

    def get_meeting_subjects(self, obj):
        subjects = obj.meeting_subject.all()
        return ", ".join(str(s) for s in subjects) if subjects.exists() else "انتخاب نشده"
    get_meeting_subjects.short_description = "موضوعات ملاقات"


@admin.register(MeetingSubject)
class MeetingSubjectAdmin(admin.ModelAdmin):
    list_display = ['name']


# ------------------------------------------------------------
# Visit
# ------------------------------------------------------------
class VisitForm(forms.ModelForm):
    class Meta:
        model = Visit
        fields = '__all__'
        widgets = {'visit_date': AdminJalaliDateWidget}

    description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 1, 'cols': 5}),
        required=False
    )


class VisitAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    form = VisitForm
    list_display = ('movakel', 'visit_date', 'start_time', 'end_time',
                    'get_duration', 'description')
    list_filter = ('visit_date',)
    search_fields = ('movakel__name', 'description')

    @admin.display(description='مدت جلسه')
    def get_duration(self, obj):
        return obj.visit_duration or 'ثبت نشده'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['visit_date'].widget = AdminJalaliDateWidget()
        return form


class VisitInline(admin.TabularInline):
    model = Visit
    extra = 0
    fields = ('visit_date', 'start_time', 'end_time', 'visit_duration', 'description')
    readonly_fields = ('visit_duration',)
    form = VisitForm

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.form.base_fields['visit_date'].widget = AdminJalaliDateWidget(
            attrs={'style': 'width: 150px;'}
        )
        formset.form.base_fields['description'].widget.attrs.update({
            'rows': 2, 'cols': 5, 'style': 'height: 4em; width: 100%;'
        })
        return formset


# ------------------------------------------------------------
# InstallmentPayment
# ------------------------------------------------------------
@admin.register(InstallmentPayment)
class InstallmentPaymentAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = ('movakel', 'amount', 'due_date_shamsi', 'payment_status')
    list_filter = ('is_paid',)

    @admin.display(description="وضعیت پرداخت")
    def payment_status(self, obj):
        if obj.is_paid:
            return format_html('<span style="color: green;">✅ پرداخت شده</span>')
        return format_html('<span style="color: red;">❌ در انتظار پرداخت</span>')

    @admin.display(description="تاریخ سررسید")
    def due_date_shamsi(self, obj):
        if obj.due_date:
            return jdate.fromgregorian(date=obj.due_date).strftime('%Y/%m/%d')
        return "-"


# ------------------------------------------------------------
# Expert
# ------------------------------------------------------------
@admin.register(Expert)
class ExpertAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = ('name', 'mobile_number', 'expertise')
    search_fields = ('name', 'mobile_number')
    ordering = ('name',)


# ------------------------------------------------------------
# ContractYearFilter
# ------------------------------------------------------------
class ContractYearFilter(admin.SimpleListFilter):
    title = "سال قرارداد"
    parameter_name = "contract_year"

    def lookups(self, request, model_admin):
        years = (Movakel.objects
                 .filter(contract_date__isnull=False)
                 .dates('contract_date', 'year'))
        return [(year.year, str(year.year)) for year in years]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(contract_date__year=self.value())
        return queryset



#--------MovakelType----------
@admin.register(MovakelType)
class MovakelTypeAdmin(admin.ModelAdmin):
    list_display = ['title', 'url_title']


# ------------------------------------------------------------
# MovakelAdmin
# ------------------------------------------------------------
@admin.register(Movakel)
class MovakelAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    form = MovakelAdminForm
    inlines = [
        ExpertInline,
        MovakelBranchArchiveInline,
        VisitInline,
        DefenseDocumentInline,
        InstallmentPaymentInline,
    ]

    list_display = [
        'name', 'total_amount_display', 'remaining_amount_display',
        'lawyer_services_fee_display', 'total_litigation_fees_display',
        'primary_archive_no', 'appeal_archive_no', 'executive_archive_no',
    ]
    list_filter = (ContractYearFilter, 'is_active', 'is_delete', 'payment_method')
    search_fields = ('name', 'mobile_number', 'file_number', 'mechanized_number')
    ordering = ('-contract_date',)

    fields = (
        'name', 'category', 'presenter', 'age',
        'mobile_number', 'file_number', 'mechanized_number',
        'image', 'pdf_files', 'description', 'slug',
        'is_active', 'is_delete', 'total_amount', 'bail_amount',
        'final_result', 'hearing_date', 'hearing_time',
        'primary_archive_no', 'primary_court_number',
        'primary_court_notification_date', 'primary_court_result', 'primary_branch',
        'appeal_court_number', 'appeal_archive_no',
        'appeal_court_notification_date', 'appeal_court_result', 'appeal_branch',
        'executive_case_number', 'executive_archive_no',
        'executive_case_notification_date', 'executive_court_result', 'executive_branch',
        'auction_date', 'contract_date',
        'stamp_tax', 'judiciary_share', 'annual_tax', 'total_tax',
    )

    readonly_fields = (
        'stamp_tax', 'judiciary_share', 'annual_tax', 'total_tax',
    )
    prepopulated_fields = {"slug": ("name",)}

    # --------------------------------------------------------
    # فیلدهای محاسباتی (readonly)
    # --------------------------------------------------------
    @admin.display(description="تمبر مالیاتی")
    def stamp_tax(self, obj):
        return format_toman(obj.stamp_tax())

    @admin.display(description="سهم مرکز وکلای قوه قضائیه")
    def judiciary_share(self, obj):
        return format_toman(obj.judiciary_share())

    @admin.display(description="مالیات سالانه")
    def annual_tax(self, obj):
        return format_toman(obj.annual_tax())

    @admin.display(description="جمع مالیات‌ها")
    def total_tax(self, obj):
        return format_toman(obj.total_tax())

    # --------------------------------------------------------
    # نمایش‌های لیست (list_display)
    # --------------------------------------------------------
    @admin.display(description="مبلغ کل")
    def total_amount_display(self, obj):
        return format_toman(obj.total_amount)

    @admin.display(description="باقی‌مانده مبلغ")
    def remaining_amount_display(self, obj):
        return format_toman(obj.remaining_amount())

    @admin.display(description="هزینه کل خدمات وکیل")
    def lawyer_services_fee_display(self, obj):
        return format_toman(obj.lawyer_services_fee)

    @admin.display(description="جمع کل هزینه دادرسی")
    def total_litigation_fees_display(self, obj):
        return format_toman(obj.total_litigation_fees)

    # --------------------------------------------------------
    # QuerySet و حذف
    # --------------------------------------------------------
    def get_queryset(self, request):
        qs = super().get_queryset(request).filter(is_delete=False)
        return qs.select_related(
            'category', 'primary_branch', 'appeal_branch', 'executive_branch'
        ).prefetch_related(
            'pdf_files', 'expert', 'branch_archives',
            'service_type', 'installment_payments',
        )

    def delete_model(self, request, obj):
        with transaction.atomic():
            MovakelPayment.objects.filter(movakel=obj).update(is_delete=True)
            Movakel.all_objects.filter(pk=obj.pk).update(is_delete=True)

    def delete_queryset(self, request, queryset):
        with transaction.atomic():
            MovakelPayment.objects.filter(movakel__in=queryset).update(is_delete=True)
            Movakel.all_objects.filter(
                pk__in=queryset.values_list('pk', flat=True)
            ).update(is_delete=True)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not obj.case_steps:
            obj.add_case_step('مرحله اولیه پرونده')

    class Media:
        js = ('admin/movakel_dynamic_price.js',)

# ------------------------------------------------------------
# ثبت‌های ساده
# ------------------------------------------------------------
admin.site.register(models.MovakelCategory)
admin.site.register(models.MovakelGallery)
admin.site.register(Branch, BranchAdmin)
admin.site.register(Visit, VisitAdmin)