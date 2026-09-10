from jalali_date.admin import ModelAdminJalaliMixin
from django.contrib import admin
from . import models
from .models import Movakel, Expert, InstallmentPayment, MeetingSubject, Visit, ServiceType, DefenseDocument, PDFFile, Branch, MovakelBranchArchive, RequestMeeting
from django import forms
from django.db.models import Sum
import jdatetime
from django.db import transaction
from .forms import MovakelAdminForm, ServiceTypeForm
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from jalali_date import datetime2jalali
from jalali_date.widgets import AdminJalaliDateWidget
from jdatetime import date as jdate




class PDFFileInline(admin.StackedInline):  # یا admin.TabularInline
    model = Movakel.pdf_files.through  # اتصال ManyToMany به‌صورت Inline
    extra = 0  # نمایش یک فیلد خالی برای افزودن فایل جدید

class MovakelAdminForm(forms.ModelForm):
    class Meta:
        model = Movakel
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        #total_amount = cleaned_data.get('total_amount', 0)
        #received_amount = cleaned_data.get('received_amount', 0)
        #payment_amount = cleaned_data.get('payment_amount', 0)
        # بررسی اینکه مبلغ پرداختی از مبلغ کل بیشتر نباشد
        #if payment_amount + received_amount > total_amount:
        #    raise forms.ValidationError("مجموع مبلغ دریافت شده و مبلغ پرداختی نمی‌تواند بیشتر از مبلغ توافق شده باشد.")
        #return cleaned_data
        # ✅ جایگزین کن
        total_amount = cleaned_data.get('total_amount') or 0
        if total_amount < 0:
            raise forms.ValidationError("مبلغ کل حق‌الوکاله نمی‌تواند منفی باشد.")
                
                
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # اضافه کردن قیمت به صورت فقط خواندنی (Read-Only)
        self.fields['service_price'] = forms.CharField(
            required=False,
            label="Price",
            widget=forms.TextInput(attrs={'readonly': 'readonly'})
        )
        self.fields['final_result'].widget = forms.Textarea(attrs={'rows': 4, 'cols': 50})

class BranchAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = ('name', 'category')  # فیلدهای نمایش داده شده در لیست
    search_fields = ('name', 'category')  # فیلدهایی که قابل جستجو هستند

class MovakelBranchArchiveInline(admin.TabularInline):  # یا admin.StackedInline
    model = MovakelBranchArchive
    extra = 0  # تعداد فرم‌های اضافی برای اضافه کردن شعبه جدید
    verbose_name = "شعبه"
    verbose_name_plural = "شعبه‌ها" 

# نمایش مدل DefenseDocument در داخل صفحه Movakel به‌صورت inline
class DefenseDocumentInline(admin.TabularInline):  # یا admin.StackedInline
    model = DefenseDocument
    extra = 0  # تعداد ردیف‌های اضافی که برای وارد کردن داده‌های جدید به‌طور پیش‌فرض نمایش داده می‌شود
    verbose_name = 'مدرک دفاعی'
    verbose_name_plural = 'مدارک دفاعی'
    fields = ('stage','subject','pdf_file','word_file')  # فیلدهایی که نمایش داده می‌شود. در اینجا 'slug' حذف شده است.

""" class HearingScheduleInline(admin.TabularInline):
    model = HearingSchedule
    extra = 0  # تعداد فرم‌های خالی برای اضافه کردن وقت جدید
    fields = ('hearing_date', 'hearing_time')  # فیلدهایی که در ادمین نمایش داده می‌شوند
    readonly_fields = []  # اگر می‌خواهید فیلدها فقط خواندنی باشند
     """
@admin.register(DefenseDocument)
class DefenseDocumentAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = ['stage','movakel']
    search_fields = ['case__movakel']

@admin.register(PDFFile)
class PDFFileAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = ['file', 'uploaded_at']

# کلاس ادمین برای مدل ServiceType
class ServiceTypeAdminForm(forms.ModelForm):
    class Meta:
        model = ServiceType
        fields = '__all__'  # Make sure the fields are correctly matched with your model

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
            field.required = False  # همه فیلدها اجباری شوند
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
        return instance

@admin.register(ServiceType)
class ServiceTypeAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    form = ServiceTypeAdminForm
    search_fields = ('movakel',)
    
    # گروه‌بندی فیلدها
    fieldsets = (
        ('موکل', {
        'fields': ('movakel',)
        }),
        ('اختیار وکیل', {
            'fields': ('office_study', 'defense', 'consultation', 'check_documents', 'contract', 'notification', 'bill', 'lawyer_services_fee')
        }),
        ('هزینه دادرسی', {
            'fields': ('bill_fee','initial_fee', 'appeal_fee', 'enforcement_fee', 'petition_fee','travel_fee',
                       'miscellaneous_fee','contract_fee','notification_fee',
                       'court_service_fee', 'document_fee','total_litigation_fees_display',)
        }),

    )

    list_display = (
        'movakel',
        'defense', 
        'consultation', 
        'check_documents', 
        'contract',
        'office_study',
        'bill',
        'lawyer_services_fee',  # نمایش هزینه کلی خدمات وکیل
        'total_litigation_fees_display',  # اضافه کردن فیلد جدید برای نمایش جمع کل هزینه دادرسی

    )
    def lawyer_services_fee(self, obj):
        return f"{obj.lawyer_services_fee:,} تومان"
    lawyer_services_fee.short_description = "هزینه کل خدمات وکیل"

    def total_litigation_fees_display(self, obj):
        return f"{obj.total_litigation_fees():,} تومان"
    total_litigation_fees_display.short_description = "جمع کل هزینه دادرسی"
    
    list_filter = ('defense', 'consultation', 'check_documents', 'contract', 'bill')
    list_editable = ('defense','office_study','consultation', 'check_documents', 'contract', 'bill')
    readonly_fields = ('total_fee_display','total_litigation_fees_display',) # اضافه کردن فیلد جمع کل هزینه دادرسی)

    @admin.display(description='Total Fee')
    def total_fee_display(self, obj):
        return obj.total_fee

    @admin.display(description='جمع کل هزینه دادرسی')
    def total_litigation_fees_display(self, obj):
        return obj.total_litigation_fees()

    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }

@admin.register(RequestMeeting)
class RequestMeetingAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = ['full_name', 'national_id', 'meeting_date_formatted', 'start_time', 'end_time', 'duration','meeting_date',]
    list_filter = ('meeting_type', 'created_at')
    search_fields = ('full_name', 'national_id')
    ordering = ('-created_at',)
    filter_horizontal = ('meeting_subject',)
    jalali_date_fields = ('meeting_date',)  # فیلدهای تاریخ شمسی
    
    def get_meeting_subjects(self, obj):
        return ", ".join(str(subject) for subject in obj.meeting_subject.all()) if obj.meeting_subject.exists() else "انتخاب نشده"
    get_meeting_subjects.short_description = "موضوعات ملاقات"

    def meeting_date_shamsi(self, obj):
        if obj.meeting_date:
            return jdatetime.datetime.fromgregorian(datetime=obj.meeting_date).strftime('%Y/%m/%d')
        return None
    meeting_date_shamsi.short_description = "تاریخ ملاقات شمسی"

@admin.register(MeetingSubject)
class MeetingSubjectAdmin(admin.ModelAdmin):
    list_display = ['name']  # نمایش نام در لیست


class VisitForm(forms.ModelForm):
    class Meta:
        model = Visit
        fields = '__all__'
        widgets = {
            'visit_date': AdminJalaliDateWidget,  # استفاده از ویجت تقویم شمسی
        }

    description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 1, 'cols': 5}),  # تنظیم ابعاد
        required=False
    )

class VisitAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    form = VisitForm
    list_display = ('movakel', 'visit_date_shamsi', 'start_time', 'end_time', 'get_duration', 'description')
    list_filter = ('visit_date',)
    search_fields = ('movakel__name', 'description')

    def visit_date_shamsi(self, obj):
        if obj.visit_date:
            return jdatetime.date.fromgregorian(date=obj.visit_date).strftime('%Y/%m/%d')
        return None
    visit_date_shamsi.short_description = "تاریخ مراجعه شمسی"
    
    def get_duration(self, obj):
        return obj.visit_duration if obj.visit_duration else 'ثبت نشده'
    get_duration.short_description = 'مدت جلسه'

    # این متد باعث می‌شود ویجت تقویم شمسی نمایش داده شود
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['visit_date'].widget = AdminJalaliDateWidget()
        return form

class VisitInline(admin.TabularInline):
    model = Visit
    extra = 0  # تعداد ردیف‌های اضافی که به‌طور پیش‌فرض نمایش داده شود
    fields = ('visit_date','start_time', 'end_time', 'visit_duration', 'description')
    readonly_fields = ('visit_duration',)
    form = VisitForm  # استفاده از فرم سفارشی
    
    def visit_date_shamsi(self, obj):
        if obj.visit_date:
            return jdatetime.date.fromgregorian(date=obj.visit_date).strftime('%Y/%m/%d')
        return None
    visit_date_shamsi.short_description = "تاریخ مراجعه شمسی"
    # تنظیم ابعاد فیلد توضیحات در اینلاین
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.form.base_fields['visit_date'].widget = AdminJalaliDateWidget(            attrs={'style': 'width: 150px;'},  # تنظیم استایل اختیاری
        )
        formset.form.base_fields['description'].widget.attrs.update({
            'rows': 2,
            'cols': 5,
            'style': 'height: 4em; width: 100%;'  # تنظیم ارتفاع و عرض
        })
        return formset


class InstallmentPaymentAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = ('movakel', 'amount', 'due_date', 'payment_status')
    list_filter = ('is_paid',)
    
    def payment_status(self, obj):
        if obj.is_paid:
            return format_html('<span style="color: green;">✅ پرداخت شده</span>')
        return format_html('<span style="color: red;">❌ در انتظار پرداخت</span>')

    payment_status.short_description = "وضعیت پرداخت"

    def due_date(self, obj):
        if obj.due_date:
            return jdate.fromgregorian(date=obj.due_date).strftime('%Y/%m/%d')
        return "-"
    due_date.short_description = "تاریخ سررسید"

    def payment_date(self, obj):
        if obj.payment_date:
            return jdate.fromgregorian(date=obj.payment_date).strftime('%Y/%m/%d')
        return "-"
    payment_date.short_description = "تاریخ پرداخت"



class InstallmentPaymentInline(admin.TabularInline):
    model = InstallmentPayment
    extra = 0
    verbose_name = 'پرداخت حق الوکاله'
    verbose_name_plural = 'پرداخت‌های حق الوکاله'
    fields = ('amount',)
    readonly_fields = ()  # اطمینان حاصل کنید که payment_date در readonly_fields نیست

    # تبدیل تاریخ شمسی در فیلدها
    def payment_date(self, obj):
        if obj.payment_date:
            return jdate.fromgregorian(date=obj.payment_date).strftime('%Y/%m/%d')
        return "-"
    payment_date.short_description = "تاریخ پرداخت"
    
    
@admin.register(Expert)
class ExpertAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = ('name','mobile_number','expertise')  # نمایش فیلدهای مهم
    search_fields = ('name', 'mobile_number')  # قابلیت جستجو برای فیلدهای خاص
    ordering = ('name',)  # مرتب‌سازی بر اساس نام کامل

class ExpertInline(admin.TabularInline):
    model = Movakel.expert.through  # ارتباط بین موکل و کارشناس (ManyToMany)
    extra = 0  # تعداد فیلدهای اضافی که در فرم نمایش داده شوند
    verbose_name = 'کارشناس'
    verbose_name_plural = 'کارشناسان'
    fields = ('expert',)  # نمایش کارشناس و تخصص

class ContractYearFilter(admin.SimpleListFilter):
    """ فیلتر نمایش موکلین بر اساس سال قرارداد """
    title = "سال قرارداد"
    parameter_name = "contract_year"

    def lookups(self, request, model_admin):
        years = Movakel.objects.filter(contract_date__isnull=False).dates('contract_date', 'year')
        return [(year.year, str(year.year)) for year in years]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(contract_date__year=self.value())
        return queryset
    
@admin.register(Movakel)
class MovakelAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    form = MovakelAdminForm
    inlines = [
        ExpertInline,
        MovakelBranchArchiveInline, 
        VisitInline, 
        DefenseDocumentInline, 
        #HearingScheduleInline,
        InstallmentPaymentInline,  # افزودن این خط به منظور نمایش اقساط در پنل Movakel
    ]
    list_display = ['name','total_amount','remaining_amount_display','lawyer_services_fee','total_litigation_fees_display','primary_archive_no', 'appeal_archive_no', 'executive_archive_no']
    list_filter = (ContractYearFilter,'is_active', 'is_delete', 'payment_method')
    search_fields = ('name', 'mobile_number', 'file_number', 'mechanized_number')
    #ordering = ('case_steps',)
    ordering = ('-contract_date',)

    fields = (
        'name', 'category', 'presenter', 'age',
        'mobile_number', 'file_number', 'mechanized_number',
        'image', 'pdf_files', 'description', 'slug',
        'is_active', 'is_delete','total_amount','bail_amount',
        'final_result', 'hearing_date', 'hearing_time', 'primary_archive_no',
        'primary_court_number', 'primary_court_notification_date', 'primary_court_result','primary_branch', 
        'appeal_court_number', 'appeal_archive_no', 'appeal_court_notification_date', 'appeal_court_result','appeal_branch',
        'executive_case_number', 'executive_archive_no', 'executive_case_notification_date', 'executive_court_result','executive_branch',        
        'auction_date','contract_date','stamp_tax', 'judiciary_share', 'annual_tax', 'total_tax'
    )

    readonly_fields = ('jalali_payment_date', 'pdf_file_links','stamp_tax','judiciary_share','annual_tax','total_tax')
    prepopulated_fields = {"slug": ("name",)}  # تولید خودکار slug از name
       # اضافه کردن فیلدهای خواندنی به فرم

    
    def stamp_tax(self, obj):
        """محاسبه تمبر مالیاتی (5% از مبلغ کل حق الوکاله)"""
        tax = obj.total_amount * 0.05
        return f"{self.format_ir_number(tax)} تومان"
    stamp_tax.short_description = "تمبر مالیاتی"

    def judiciary_share(self, obj):
        """محاسبه سهم قوه قضاییه (5% از مبلغ کل حق الوکاله)"""
        share = obj.total_amount * 0.05
        return f"{self.format_ir_number(share)} تومان"
    judiciary_share.short_description = "سهم مرکز وکلای قوه قضائیه "

    def annual_tax(self, obj):
        """محاسبه مالیات پایان سال (25% از مبلغ کل حق الوکاله)"""
        tax = obj.total_amount * 0.25
        return f"{self.format_ir_number(tax)} تومان"
    annual_tax.short_description = "مالیات سالانه"

    def total_tax(self, obj):
        """مجموع تمام مالیات‌ها"""
        total = (obj.total_amount * 0.05) + (obj.total_amount * 0.05) + (obj.total_amount * 0.25)
        return f"{self.format_ir_number(total)} تومان"
    total_tax.short_description = "جمع مالیات‌ها"

    def format_ir_number(self, number):
        """فرمت‌دهی اعداد به صورت فارسی با جداکننده سه‌رقمی (پشتیبانی از اعشار)"""
        if number is None:
            return "۰"
        
        if isinstance(number, float):
            # برای اعداد اعشاری، بخش صحیح و اعشار را جداگانه فرمت می‌کنیم
            integer_part, decimal_part = str(number).split('.')
            formatted_int = "{:,}".format(int(integer_part))
            return f"{formatted_int.translate(self.translation_table)}.{decimal_part.translate(self.translation_table)}"
        else:
            formatted = "{:,}".format(int(number))
            return formatted.translate(self.translation_table)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.translation_table = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')



    @admin.display(description="سال قرارداد")
    def contract_year_display(self, obj):
        return obj.contract_date.year if obj.contract_date else "نامشخص"
    
    @admin.display(description="باقی‌مانده مبلغ")
    def remaining_amount_display(self, obj):
        return obj.remaining_amount()
    
    def lawyer_services_fee(self, obj):
        service = obj.service_type
        return f"{service.lawyer_services_fee:,} تومان" if service else "نامشخص"
    lawyer_services_fee.short_description = "هزینه کل خدمات وکیل"

    def total_litigation_fees_display(self, obj):
        service = obj.service_type
        return f"{service.total_litigation_fees():,} تومان" if service else "نامشخص"
    total_litigation_fees_display.short_description = "جمع کل هزینه دادرسی"
    
    def branch_display(self, obj):
        branch_info = ", ".join([  # نمایش شعبه‌های مرتبط
            f"شعبه {archive.branch.name} {archive.branch.category} شماره بایگانی {archive.archive_no}"
            for archive in obj.branch_archives.all()
        ])
        return branch_info

    def pdf_file_links(self, obj):
        """نمایش لینک دانلود فایل‌های PDF مرتبط"""
        pdfs = obj.pdf_files.all()
        if not pdfs:
            return "هیچ فایلی موجود نیست"
        links = [f'<a href="{pdf.file.url}" target="_blank">{pdf.file.name}</a>' for pdf in pdfs]
        return mark_safe("<br>".join(links))

    def total_payment(self, obj):
        total_paid = obj.movakelpayments.filter(is_delete=False).aggregate(total_payment=Sum('amount'))['total_payment'] or 0
        return total_paid

    def remaining_amount(self, obj):
        """باقی‌مانده مبلغ — از متد مدل استفاده می‌شود"""
        return obj.remaining_amount()
    remaining_amount.short_description = 'باقی مانده'

    def jalali_payment_date(self, obj):
        if obj.payment_date:
            return obj.payment_date.strftime('%Y/%m/%d')

    def delete_model(self, request, obj):
        with transaction.atomic():
            obj.movakelpayments.all().update(is_delete=True)
            obj.delete()  # حذف منطقی (تنها تغییر مقدار is_delete)

    def get_queryset(self, request):
        queryset = super().get_queryset(request).filter(is_delete=False)
        return queryset

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # در صورتی که نیاز به افزودن مرحله به صورت خودکار باشد
        if not obj.case_steps:
            obj.add_case_step('مرحله اولیه پرونده')

    class Media:
        js = ('admin/movakel_dynamic_price.js',)  # فایل JavaScript سفارشی



class Media:
    js = [
        'jalali_date/js/jquery.min.js',
        'jalali_date/js/jalali_date.min.js',
        'admin/js/jalali_calendar_setup.js',  # اگر تقویم سفارشی داری
    ]
    css = {
        'all': ['admin/css/jalali_admin.css']
    }

admin.site.register(models.MovakelCategory)
admin.site.register(models.MovakelGallery)
admin.site.register(Branch, BranchAdmin)
admin.site.register(InstallmentPayment, InstallmentPaymentAdmin)
