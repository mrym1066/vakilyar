import jdatetime
from django import forms
from .models import Movakel,RequestMeeting,ServiceType,MeetingSubject,MovakelCategory
from datetime import datetime, timedelta,date
from jalali_date.fields import JalaliDateField
from jalali_date.widgets import AdminJalaliDateWidget


class MovakelAdminForm(forms.ModelForm):
    class Meta:
        model = Movakel
        fields = '__all__'
   
    def clean(self):
        cleaned_data = super().clean()
        total_amount = cleaned_data.get('total_amount') or 0
        if total_amount < 0:
            raise forms.ValidationError("مبلغ کل حق‌الوکاله نمی‌تواند منفی باشد.")
        return cleaned_data

    #def clean(self):
    #    cleaned_data = super().clean()
    #    total_amount = cleaned_data.get('total_amount', 0)
    #    received_amount = cleaned_data.get('received_amount', 0)
    #    if received_amount > total_amount:
    #        raise forms.ValidationError("مبلغ دریافت شده نمی‌تواند بیشتر از مبلغ توافق شده باشد.")
    #   return cleaned_data

class DamageCalculationForm(forms.Form):
    original_amount = forms.DecimalField(label="مبلغ بدهی (ریال)", min_value=0)
    due_date = forms.DateField(
        label="تاریخ سررسید",
        widget=AdminJalaliDateWidget
    )
    payment_date = forms.DateField(
        label="تاریخ پرداخت",
        widget=AdminJalaliDateWidget
    )
    inflation_rate = forms.FloatField(label="نرخ تورم (درصد)", min_value=0)


class MovakelForm(forms.ModelForm):
    class Meta:
        model = Movakel
        fields = [
            'name', 'age', 'mobile_number', 'mechanized_number', 'file_number', 
            'image', 'pdf_files'
            ]

    def __init__(self, *args, **kwargs):
        request_meeting = kwargs.pop('request_meeting', None)
        super().__init__(*args, **kwargs)

        if request_meeting:
            self.fields['name'].initial = request_meeting.full_name
            self.fields['mobile_number'].initial = request_meeting.mobile_number
            self.fields['file_number'].initial = request_meeting.phone_number

    
class ServiceTypeForm(forms.ModelForm):

    class Meta:
        model = ServiceType
        exclude = ['movakel']
        #fields = (
        #    'defense', 'consultation', 'check_documents', 'office_study',
        #    'contract', 'bill', 'notification'
        #)
        widgets = {
            'defense': forms.CheckboxInput(attrs={'class': 'inline-checkbox'}),
            'consultation': forms.CheckboxInput(attrs={'class': 'inline-checkbox'}),
            'check_documents': forms.CheckboxInput(attrs={'class': 'inline-checkbox'}),
            'office_study': forms.CheckboxInput(attrs={'class': 'inline-checkbox'}),
            'contract': forms.CheckboxInput(attrs={'class': 'inline-checkbox'}),
            'bill': forms.CheckboxInput(attrs={'class': 'inline-checkbox'}),
            'notification': forms.CheckboxInput(attrs={'class': 'inline-checkbox'}),

        }

    class Media:
        css = {
            'all': ('static/admin/css/custom_admin.css',)  # اضافه کردن استایل‌ها به بخش ادمن
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # بررسی مقدار هزینه‌ها و تنظیم هزینه مشترک
        for field in self.fields.values():
            field.required = False  # همه فیلدها اجباری شوند

    def save(self, commit=True):
        instance = super().save(commit=False)
    # فرض می‌کنیم که می‌خواهیم هزینه‌ها را از فرم به‌صورت مستقیم تنظیم کنیم
        instance.travel_fee = self.cleaned_data.get('travel_fee', 0)
        instance.miscellaneous_fee = self.cleaned_data.get('miscellaneous_fee', 0)
        instance.office_study_fee = self.cleaned_data.get('office_study_fee', 0)
        instance.contract_fee = self.cleaned_data.get('contract_fee', 0)
        instance.bill_fee = self.cleaned_data.get('bill_fee', 0)
        instance.appeal_fee = self.cleaned_data.get('appeal_fee', 0)  # اضافه کردن appeal_fee
        instance.enforcement_fee = self.cleaned_data.get('enforcement_fee', 0)  # Ensure default value if not provided
        instance.court_service_fee = self.cleaned_data.get('court_service_fee', 0)  # Ensure default value if not provided
        instance.petition_fee = self.cleaned_data.get('petition_fee', 0)  # Set default value if not provided
        instance.document_fee = self.cleaned_data.get('document_fee', 0)  # Set default value if not provided

        if commit:
            instance.save()
        return instance


class RequestMeetingForm(forms.ModelForm):

    meeting_subject = forms.ModelMultipleChoiceField(
        queryset=MeetingSubject.objects.all(),
        widget=forms.CheckboxSelectMultiple,  # 👈 افزودن استایل
        required=False,
        label="موضوع ملاقات"
    )
    meeting_date = JalaliDateField(
        widget=AdminJalaliDateWidget,  # ویجت مخصوص نمایش تاریخ شمسی
        required=True,
        label="تاریخ ملاقات"
    )
    # حذف فیلدهای تاریخ؛ فقط زمان ورود و خروج باقی می‌مانند
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time'}),
        required=True,
        label="زمان ورود"
    )
    end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time'}),
        required=True,
        label="زمان خروج"
    )
    duration = forms.CharField(
        widget=forms.TextInput(attrs={'readonly': 'readonly', 'id': 'duration'}),  # 👈 فقط خواندنی
        required=False,
        label="مدت جلسه"
    )
    virtual_number = forms.CharField(
        max_length=11,
        required=False,
        label="شماره فضای مجازی"
    )
    birth_date = JalaliDateField(
        widget=AdminJalaliDateWidget,
        required=True,
        label="تاریخ تولد"
    )
    identification_number = forms.CharField(
        required=False,  # 👈 اختیاری
        label="شماره شناسنامه"
    )
    phone_number = forms.CharField(
        required=False,  # 👈 اختیاری
        max_length=11,  # محدودیت حداکثر طول 11 رقم
        label="تلفن ثابت"

    )
    email = forms.EmailField(
        required=False,  # 👈 اختیاری
        label="ایمیل"
    )
    address = forms.CharField(
        required=False,  # 👈 اختیاری
        widget=forms.Textarea(attrs={'rows': 2}),
        label="آدرس"
    )
    postal_code = forms.CharField(
        required=False,  # 👈 اختیاری
        max_length=10,  # محدودیت حداکثر طول 10 رقم
        label="کدپستی"
    )
    
    class Meta:
        model = RequestMeeting
        fields = [
            'full_name', 'national_id', 'identification_number', 'birth_date',
            'phone_number', 'mobile_number', 'email', 'address', 'postal_code',
            'meeting_type', 'meeting_subject','meeting_date','virtual_number',
            'start_time', 'end_time', 'meeting_fee','duration'
        ]
        widgets = {
            'meeting_type': forms.Select(choices=RequestMeeting.MEETING_TYPES),  # اضافه کردن `choices`
        }
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if start_time and end_time:
            today = date.today()
            start_datetime = datetime.combine(today, start_time)
            end_datetime = datetime.combine(today, end_time)
            duration = (end_datetime - start_datetime).seconds // 60
            cleaned_data['duration'] = f"{duration} دقیقه" if duration > 0 else "کمتر از ۱ دقیقه"

        return cleaned_data

    def save(self, commit=True, *args, **kwargs):
        instance = super().save(commit=False, *args, **kwargs)

        # اگر مدت زمان محاسبه شده بود، ذخیره کن
        if self.cleaned_data.get('duration'):
            instance.duration = self.cleaned_data['duration']

        # موضوع جدید (در صورت وجود) را ذخیره کن
        new_subject_name = self.cleaned_data.get("new_subject")
        if new_subject_name:
            # بررسی می‌کنیم که آیا این موضوع قبلاً ایجاد نشده
            subject, created = MeetingSubject.objects.get_or_create(name=new_subject_name)
            # اگر commit نشده، اول ذخیره کن تا بتوان ManyToMany را استفاده کرد
            if not instance.pk:
                instance.save()
            instance.meeting_subject.add(subject)

        if commit:
            instance.save()
            self.save_m2m()

        return instance
        

        
# ============================================================
# فرم‌های ویرایش اطلاعات موجود در صفحه جزئیات موکل
# ============================================================
from .models import Visit, DefenseDocument, PDFFile


class VisitEditForm(forms.ModelForm):
    class Meta:
        model = Visit
        fields = ['visit_date', 'start_time', 'end_time', 'description']
        widgets = {
            'visit_date': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '۱۴۰۵/۰۶/۱۲',
                'dir': 'ltr',
            }),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.start_time and instance.end_time:
            start_minutes = instance.start_time.hour * 60 + instance.start_time.minute
            end_minutes = instance.end_time.hour * 60 + instance.end_time.minute
            duration = end_minutes - start_minutes
            if duration > 0:
                instance.visit_duration = f'{duration} دقیقه'
            elif duration == 0:
                instance.visit_duration = 'کمتر از ۱ دقیقه'
            else:
                instance.visit_duration = 'زمان پایان نامعتبر'
        else:
            instance.visit_duration = None
        if commit:
            instance.save()
        return instance


class DefenseDocumentEditForm(forms.ModelForm):
    class Meta:
        model = DefenseDocument
        fields = ['stage', 'subject', 'pdf_file', 'word_file']
        widgets = {
            'stage': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'pdf_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'word_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class PDFFileEditForm(forms.ModelForm):
    class Meta:
        model = PDFFile
        fields = ['name', 'file']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class MovakelBasicEditForm(forms.ModelForm):
    """ویرایش اطلاعات اصلی قابل مشاهده در صفحه موکل."""
    contract_date = JalaliDateField(
        widget=AdminJalaliDateWidget,
        required=False,
        label='تاریخ وکالت',
    )

    class Meta:
        model = Movakel
        fields = [
            'name', 'presenter', 'age', 'mobile_number', 'file_number',
            'mechanized_number', 'category', 'image', 'description',
            'is_active', 'case_status', 'payment_method', 'final_result',
            'total_amount', 'bail_amount', 'contract_date', 'file',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'presenter': forms.TextInput(attrs={'class': 'form-control'}),
            'age': forms.TextInput(attrs={'class': 'form-control'}),
            'mobile_number': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'file_number': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'mechanized_number': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'case_status': forms.Select(attrs={'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'final_result': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'bail_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def clean_total_amount(self):
        value = self.cleaned_data.get('total_amount') or 0
        if value < 0:
            raise forms.ValidationError('مبلغ کل حق‌الوکاله نمی‌تواند منفی باشد.')
        return value


class CourtInfoEditForm(forms.ModelForm):
    """فرم مستقل برای ویرایش اطلاعات جدول دادگاه؛ بدون دست‌کاری سایر اطلاعات موکل."""
    hearing_date = JalaliDateField(widget=AdminJalaliDateWidget, required=False, label='وقت رسیدگی / وقت نظارت')
    primary_court_notification_date = JalaliDateField(widget=AdminJalaliDateWidget, required=False, label='تاریخ ابلاغ بدوی')
    appeal_court_notification_date = JalaliDateField(widget=AdminJalaliDateWidget, required=False, label='تاریخ ابلاغ تجدیدنظر')
    executive_case_notification_date = JalaliDateField(widget=AdminJalaliDateWidget, required=False, label='تاریخ ابلاغ اجرائیه پرونده')
    auction_date = JalaliDateField(widget=AdminJalaliDateWidget, required=False, label='تاریخ مزایده')

    class Meta:
        model = Movakel
        fields = [
            'primary_branch', 'hearing_date', 'hearing_time',
            'primary_archive_no', 'primary_court_number',
            'primary_court_notification_date', 'primary_court_result',
            'appeal_branch', 'appeal_archive_no', 'appeal_court_number',
            'appeal_court_notification_date', 'appeal_court_result',
            'executive_branch', 'executive_archive_no', 'executive_case_number',
            'executive_case_notification_date', 'auction_date', 'executive_court_result',
            'final_result',
        ]
        widgets = {
            'primary_branch': forms.Select(attrs={'class': 'form-control'}),
            'appeal_branch': forms.Select(attrs={'class': 'form-control'}),
            'executive_branch': forms.Select(attrs={'class': 'form-control'}),
            'hearing_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'primary_archive_no': forms.TextInput(attrs={'class': 'form-control'}),
            'primary_court_number': forms.TextInput(attrs={'class': 'form-control'}),
            'primary_court_result': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'appeal_archive_no': forms.TextInput(attrs={'class': 'form-control'}),
            'appeal_court_number': forms.TextInput(attrs={'class': 'form-control'}),
            'appeal_court_result': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'executive_archive_no': forms.TextInput(attrs={'class': 'form-control'}),
            'executive_case_number': forms.TextInput(attrs={'class': 'form-control'}),
            'executive_court_result': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'final_result': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class MovakelNotesEditForm(forms.ModelForm):
    class Meta:
        model = Movakel
        fields = ['description']
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 8}),
        }

class RequestMeetingEditForm(RequestMeetingForm):
    """نسخه مخصوص ویرایش ملاقات؛ ارتباط ملاقات با موکل حفظ می‌شود."""
    status = forms.ChoiceField(
        choices=RequestMeeting.STATUS_CHOICES,
        required=True,
        label='وضعیت درخواست',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    class Meta(RequestMeetingForm.Meta):
        fields = [
            'status', 'full_name', 'national_id', 'identification_number', 'birth_date',
            'phone_number', 'mobile_number', 'email', 'address', 'postal_code',
            'meeting_type', 'meeting_subject', 'meeting_date', 'virtual_number',
            'start_time', 'end_time', 'meeting_fee', 'duration',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('birth_date', 'meeting_date', 'start_time', 'end_time'):
            if name in self.fields:
                self.fields[name].required = False
