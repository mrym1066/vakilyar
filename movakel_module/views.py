from django.db.models import Count
from django.http import HttpRequest,JsonResponse,HttpResponse
from django.shortcuts import render, redirect,get_object_or_404
from django.views.generic import ListView, DetailView
from django.views.generic.base import View
from utils.http_service import get_client_ip
from utils.convertors import group_list
from .models import Movakel, MovakelCategory,InstallmentPayment,MovakelGallery,MovakelPayment,ServiceType,DefenseDocument,Branch,RequestMeeting,PaymentDetail,Visit#HearingSchedule
from .forms import (
    DamageCalculationForm, RequestMeetingForm, ServiceTypeForm,
    RequestMeetingEditForm, VisitEditForm, DefenseDocumentEditForm,
    PDFFileEditForm, MovakelBasicEditForm, CourtInfoEditForm,
    MovakelNotesEditForm,
)
from .utils import calculate_damage
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.db import transaction
from django.db.models import Sum
import tempfile
from django.template.loader import render_to_string
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import urllib.parse  # برای حل مشکل نام فارسی در نام فایل
import os
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from urllib.parse import quote
from django.conf import settings
#from celery import current_app, uuid
import uuid
import re
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.oxml import OxmlElement, ns
from django.db.models import Sum, F
import jdatetime
from datetime import datetime, date, time
from django.contrib import messages
from django.utils.dateparse import parse_datetime
from decimal import Decimal
from collections import defaultdict
import jalali_date
from django.db.models import Q
from django.http import FileResponse
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    BIDI_AVAILABLE = True
except ImportError:
    BIDI_AVAILABLE = False
from movakel_module.backup_utils import create_backup, get_all_backups, delete_backup
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from site_module.models import SiteSetting




# ============================================================
# ✅ اضافه کردن تابع بررسی ادمین بودن 
# ============================================================

def is_admin(user):
    """بررسی اینکه کاربر ادمین است یا نه"""
    return user.is_authenticated and user.is_superuser

#movakels = Movakel.objects.filter(is_delete=False)

@method_decorator(login_required(login_url='/login/'), name='dispatch')
class MovakelListView(ListView):
    template_name = 'movakel_module/movakel_list.html'
    model = Movakel
    context_object_name = 'movakels'
    ordering = ['-contract_date']
    paginate_by = 6

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request
        context['start_total_amount'] = self.request.GET.get('start_total_amount') or 0
        total_received_amount = 0

        start_total_amount = request.GET.get('start_total_amount')
        end_total_amount = request.GET.get('end_total_amount')
        movakels = Movakel.objects.filter(is_delete=False).order_by('-contract_date')

        if start_total_amount:
            movakels = movakels.filter(total_amount__gte=start_total_amount)
        if end_total_amount:
            movakels = movakels.filter(total_amount__lte=end_total_amount)

        # ============================================
        # دسته‌بندی پرونده‌ها بر اساس سال شمسی
        # ============================================
        categorized_movakels = defaultdict(list)
        for movakel in movakels:
            # اگر تاریخ قرارداد وجود داشته باشد
            if movakel.contract_date:
                try:
                    # تبدیل تاریخ میلادی به شمسی
                    shamsi_date = jdatetime.date.fromgregorian(date=movakel.contract_date)
                    year = shamsi_date.year  # سال شمسی
                except Exception as e:
                    # اگر تبدیل ناموفق بود، از سال میلادی استفاده کن
                    year = movakel.contract_date.year
            else:
                # اگر تاریخ وجود نداشت، از سال جاری استفاده کن
                year = jdatetime.date.today().year
            
            categorized_movakels[year].append(movakel)

        # مرتب‌سازی سال‌ها به صورت نزولی (جدیدترین اول)
        categorized_movakels = dict(sorted(categorized_movakels.items(), reverse=True))

        # دریافت دسته‌بندی‌ها و تعداد هر کدام
        categories = MovakelCategory.objects.all()
        category_counts = Movakel.objects.filter(is_delete=False).values('category__title').annotate(count=Count('id'))
        category_counts_dict = {item['category__title']: item['count'] for item in category_counts}

        context['category_list'] = [
            {'name': category.title, 'count': category_counts_dict.get(category.title, 0)}
            for category in categories
        ]

        context['start_total_amount'] = start_total_amount
        context['end_total_amount'] = end_total_amount
        context['categorized_movakels'] = dict(categorized_movakels)

        return context

    def get_queryset(self):
        query = super(MovakelListView, self).get_queryset()
        category_name = self.kwargs.get('cat')
        type_name = self.kwargs.get('type')

        if type_name is not None:
            query = query.filter(type__url_title__iexact=type_name)

        if category_name is not None:
            query = query.filter(category__url_title__iexact=category_name)

        return query


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class MovakelDetailView(LoginRequiredMixin, UserPassesTestMixin,DetailView):
    template_name = 'movakel_module/movakel_detail.html'
    model = Movakel
    context_object_name = 'movakel'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def test_func(self):   
        """فقط ادمین‌ها اجازه دسترسی دارند"""
        return self.request.user.is_authenticated and self.request.user.is_superuser

    def handle_no_permission(self):   
        """در صورت عدم دسترسی، به صفحه خطا هدایت کن"""
        return render(self.request, 'errors/access_denied.html', status=403)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        movakel = self.get_object()

        # فایل‌های PDF
        context['pdf_files'] = movakel.pdf_files.all()

        # پرداخت‌ها
        payments = movakel.movakelpayments.filter(is_delete=False)
        total_received_amount = payments.aggregate(total=Sum('amount'))['total'] or 0
        context['total_received_amount'] = total_received_amount

        payments_by_category = payments.values('payment_for').annotate(total=Sum('amount'))
        context['payments_by_category'] = payments_by_category

        # نوع خدمت
        try:
            service_type = movakel.service_type
        except ServiceType.DoesNotExist:
            service_type = None

        context['selected_service_type'] = service_type

        if service_type:
            context['total_service_fee'] = service_type.total_fee
        else:
            context['total_service_fee'] = 0

        # دریافت لایحه‌ها
        context['defense_documents'] = DefenseDocument.objects.filter(movakel=movakel)

        # اطلاعات دادگاه
        context['hearing_date'] = movakel.hearing_date
        context['primary_court_number'] = movakel.primary_court_number
        context['primary_court_notification_date'] = movakel.primary_court_notification_date
        context['appeal_court_number'] = movakel.appeal_court_number
        context['appeal_court_notification_date'] = movakel.appeal_court_notification_date
        context['executive_case_number'] = movakel.executive_case_number
        context['executive_case_notification_date'] = movakel.executive_case_notification_date
        context["mechanized_number"] = movakel.mechanized_number

        # دریافت لیست ملاقات‌ها
        context["meetings"] = movakel.meetings.all()

        # محاسبه مجموع هزینه ملاقات‌ها
        total_meeting_fee = movakel.meetings.aggregate(total_fee=Sum('meeting_fee'))['total_fee'] or 0
        context['total_meeting_fee'] = total_meeting_fee

        # ============================================================
        # پرونده‌های مرتبط بر اساس کد ملی و نام و نام خانوادگی
        # ============================================================
        related_movakels = Movakel.objects.filter(
            is_delete=False
        ).exclude(
            id=movakel.id
        )

        # فیلتر بر اساس کد ملی (اگر وجود داشته باشد)
        if movakel.national_id:
            related_movakels = related_movakels.filter(
                Q(national_id=movakel.national_id) |
                Q(name__icontains=movakel.name)
            )
        else:
            # اگر کد ملی وجود نداشت، فقط بر اساس نام فیلتر کن
            related_movakels = related_movakels.filter(
                name__icontains=movakel.name
            )

        # مرتب‌سازی بر اساس تاریخ قرارداد (جدیدترین اول)
        related_movakels = related_movakels.order_by('-contract_date')

        # دسته‌بندی به گروه‌های ۳ تایی برای نمایش در کاروسل
        context["related_movakels"] = [related_movakels[i:i + 3] for i in range(0, len(related_movakels), 3)]

        # دریافت وقت‌های رسیدگی
        context['visits'] = movakel.visits.all().order_by('visit_date')

        total_paid = InstallmentPayment.objects.filter(movakel=movakel).aggregate(total=Sum('amount'))['total'] or 0

        context['installment_payments'] = movakel.installment_payments.all() if hasattr(movakel, 'installment_payments') else []
        context['payments'] = movakel.movakelpayments.filter(is_delete=False).order_by('-payment_date')
        return context



@login_required(login_url='/login/')
def meeting_list_view(request):
    meetings = RequestMeeting.objects.all()
    for meeting in meetings:
        print(f"meeting_date: {meeting.meeting_date} ({type(meeting.meeting_date)})")  # 👈 بررسی مقدار


        # اگر مقدار تاریخ از نوع رشته باشد، سعی در تبدیل آن به datetime می‌کنیم
        if isinstance(meeting.meeting_date, str):
            try:
                meeting.meeting_date = parse_datetime(meeting.meeting_date)  # استفاده از parse_datetime برای تبدیل
            except ValueError as e:
                print(f"Error parsing date: {e}")  # 👈 چاپ خطای دقیق
                meeting.meeting_date = None

        # اگر مقدار تاریخ از نوع datetime باشد
        if isinstance(meeting.meeting_date, datetime):
            try:
                # تبدیل تاریخ میلادی به شمسی
                jalali_datetime = jdatetime.datetime.fromgregorian(datetime=meeting.meeting_date)
                meeting.meeting_date_shamsi = jalali_datetime.strftime('%Y/%m/%d')
                meeting.formatted_time = jalali_datetime.strftime('%H:%M')
            except Exception as e:
                print(f"Error converting datetime: {e}")
                meeting.meeting_date_shamsi = "-"
                meeting.formatted_time = "-"
        else:
            meeting.meeting_date_shamsi = "-"
            meeting.formatted_time = "-"


        meeting.meeting_fee = meeting.meeting_fee if meeting.meeting_fee is not None else 0
        meeting.subjects_display = ", ".join([subject.name for subject in meeting.meeting_subject.all()])

    context = {'meetings': meetings}
    return render(request, 'movakel_module/meetings.html', context)


def request_meeting_view(request, meeting_id=None):
    
    meeting = None
    if meeting_id:
        meeting = get_object_or_404(RequestMeeting, id=meeting_id)

    # گرفتن یک نمونه از مدل Movakel (به فرض اینکه مدل Movakel مربوط به همان پرونده است)
    #movakel_instance = Movakel.objects.get(id=1)  # این رو مطابق با شرایط پروژه تغییر بده
        # ارسال تاریخ شمسی به قالب
    #shamsi_date = movakel_instance.shamsi_date

    if request.method == "POST":
        form = RequestMeetingForm(request.POST, instance=meeting)
        if form.is_valid():
            form.save()  # ذخیره اطلاعات
            messages.success(request, "✅ قرار ملاقات با موفقیت ثبت شد.")
            return redirect("meeting_list")
        else:
            print(form.errors)  # خطاها

    else:
        form = RequestMeetingForm(instance=meeting)

        shamsi_date = jdatetime.date.today().strftime("%Y/%m/%d")
    return render(request, "movakel_module/request_meeting.html",{
        "form": form, 
        "meeting": meeting,
        "shamsi_date": shamsi_date  # اضافه کردن تاریخ شمسی به قالب

                   })


def create_request_meeting(request):
    if request.method == 'POST':
        form = RequestMeetingForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ درخواست ملاقات با موفقیت ثبت شد.')
            return redirect('meeting_list')
    else:
        form = RequestMeetingForm()

    return render(request, 'movakel_module/request_meeting_form.html', {'form': form})


@login_required(login_url='/login/')
def movakel_edit(request, slug):
    movakel = get_object_or_404(Movakel, slug=slug, is_delete=False)
    if request.method == 'POST':
        # به‌روزرسانی شماره بایگانی شعبات
        for movakel_branch in movakel.branch_archives.all():
            archive_no_key = f"archive_no_{movakel_branch.id}"
            new_archive_no = request.POST.get(archive_no_key)
            if new_archive_no:
                movakel_branch.archive_no = new_archive_no
                movakel_branch.save()

        # ویرایش اطلاعات اصلی موکل
        form = MovakelForm(request.POST, request.FILES, instance=movakel)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ پرونده با موفقیت ویرایش شد.')
            return redirect('movakel-detail', slug=movakel.slug)
    else:
        form = MovakelForm(instance=movakel)
    return render(request, 'movakel_module/movakel_edit.html', {'form': form, 'movakel': movakel})

def movakel_categories_component(request: HttpRequest):
    movakel_categories = MovakelCategory.objects.all()
    context = {
        'categories': movakel_categories
    }
    return render(request, 'movakel_module/components/movakel_categories_component.html', context)

def calculate_damage_view(request):
    result = None
    if request.method == "POST":
        form = DamageCalculationForm(request.POST)
        if form.is_valid():
            original_amount = form.cleaned_data["original_amount"]
            due_date = form.cleaned_data["due_date"]
            payment_date = form.cleaned_data["payment_date"]
            inflation_rate = form.cleaned_data["inflation_rate"]
            # محاسبه خسارت با فرمول دلخواه
            result = calculate_damage(original_amount, due_date, payment_date, inflation_rate)
        else:
            print("خطاهای فرم:", form.errors)
            result = "خطا در محاسبه خسارت"
    else:
        form = DamageCalculationForm()
    return render(request, "movakel_module/calculate_damage.html", {"form": form, "result": result})

@login_required(login_url='/login/')
def delete_movakel(request, movakel_id):
    # پیدا کردن رکورد Movakel
    movakel_instance = get_object_or_404(Movakel, id=movakel_id)
    # شروع تراکنش
    with transaction.atomic():
        # حذف رکورد Movakel و رکوردهای وابسته به آن
        movakel_instance.movakelpayments.all().update(is_delete=True)
        movakel_instance.is_delete = True  # خود پرونده هم حذف منطقی بشه
        #movakelpayments.all().update(is_delete=True) # type: ignore
        movakel_instance.save()

    return redirect('movakel_list')  # به صفحه لیست پرونده‌ها هدایت می‌کند

def get_service_price(request, service_type_id):
    try:
        service_type = ServiceType.objects.get(id=service_type_id)
        price = getattr(service_type, 'price', None)
        if price is None:
            return JsonResponse({'error': 'Price field not found'}, status=400)
        return JsonResponse({'price': price})
    except ServiceType.DoesNotExist:
        return JsonResponse({'error': 'Service type not found'}, status=404)

def service_type_detail(request, service_type_id):
    service_type = get_object_or_404(ServiceType, id=service_type_id)
    form = ServiceTypeForm(instance=service_type)

    if request.method == 'POST':
        # بروزرسانی وضعیت چک‌باکس‌ها
        service_type.office_study = 'office_study' in request.POST
        service_type.defense = 'defense' in request.POST
        service_type.consultation = 'consultation' in request.POST
        service_type.check_documents = 'check_documents' in request.POST
        service_type.contract = 'contract' in request.POST
        service_type.notification = 'notification' in request.POST
        service_type.bill = 'bill' in request.POST
        
        # بروزرسانی هزینه‌ها با مقادیر پیش‌فرض 0 اگر وجود نداشتند
        service_type.bill_fee = Decimal(request.POST.get('bill_fee', 0))
        service_type.initial_fee = Decimal(request.POST.get('initial_fee', 0))
        service_type.appeal_fee = Decimal(request.POST.get('appeal_fee', 0))
        service_type.enforcement_fee = Decimal(request.POST.get('enforcement_fee', 0))
        service_type.petition_fee = Decimal(request.POST.get('petition_fee', 0))
        service_type.travel_fee = Decimal(request.POST.get('travel_fee', 0))
        service_type.miscellaneous_fee = Decimal(request.POST.get('miscellaneous_fee', 0))
        service_type.contract_fee = Decimal(request.POST.get('contract_fee', 0))
        service_type.notification_fee = Decimal(request.POST.get('notification_fee', 0))
        service_type.court_service_fee = Decimal(request.POST.get('court_service_fee', 0))
        service_type.document_fee = Decimal(request.POST.get('document_fee', 0))
        
        service_type.save()
        return redirect('movakel-detail', slug=service_type.movakel.slug)

    return render(request,  'movakel_module/service_type_detail.html', {'service_type': service_type,'form':form,})

def update_services(request, movakel_id):
    movakel = get_object_or_404(Movakel, id=movakel_id)
    
    if request.method == 'POST':
        # بروزرسانی وضعیت چک‌باکس‌ها
        movakel.service_type.defense = 'defense' in request.POST
        movakel.service_type.consultation = 'consultation' in request.POST
        movakel.service_type.check_documents = 'check_documents' in request.POST
        movakel.service_type.contract = 'contract' in request.POST
        movakel.service_type.office_study = 'office_study' in request.POST
        movakel.service_type.bill = 'bill' in request.POST
        movakel.service_type.notification = 'notification' in request.POST

        # بروزرسانی هزینه‌ها
        try:
            movakel.service_type.travel_fee = Decimal(request.POST.get('travel_fee', 0))
            movakel.service_type.miscellaneous_fee = Decimal(request.POST.get('miscellaneous_fee', 0))
            movakel.service_type.office_study_fee = Decimal(request.POST.get('office_study_fee', 0))
            movakel.service_type.contract_fee = Decimal(request.POST.get('contract_fee', 0))
            movakel.service_type.bill_fee = Decimal(request.POST.get('bill_fee', 0))
            movakel.service_type.initial_fee = Decimal(request.POST.get('initial_fee', 0))
            movakel.service_type.appeal_fee = Decimal(request.POST.get('appeal_fee', 0))
            movakel.service_type.enforcement_fee = Decimal(request.POST.get('enforcement_fee', 0))
            movakel.service_type.petition_fee = Decimal(request.POST.get('petition_fee', 0))
            movakel.service_type.court_service_fee = Decimal(request.POST.get('court_service_fee', 0))
            movakel.service_type.document_fee = Decimal(request.POST.get('document_fee', 0))
            movakel.service_type.notification_fee = Decimal(request.POST.get('notification_fee', 0))
        except ValueError as e:
            print("خطا در تبدیل هزینه‌ها:", e)
        
        movakel.service_type.save()
        
    return redirect('movakel-detail', slug=movakel.slug)


def service_type_edit(request, pk):
    service_type = get_object_or_404(ServiceType, pk=pk)

    if request.method == "POST":
        form = ServiceTypeForm(request.POST, instance=service_type)
        if form.is_valid():
            form.save()
            return redirect("movakel-detail", slug=service_type.movakel.slug)
    else:
        form = ServiceTypeForm(instance=service_type)

    return render(request, "movakel_module/service_type_detail.html", {
        "form": form,
        "service_type": service_type,
    })

def defense_document_detail(request, pk):
    doc = get_object_or_404(DefenseDocument, pk=pk)
    return render(request, "movakel_module/defense_document_detail.html", {"doc": doc})

def download_document_word(request, pk):
    # دریافت سند دفاعی
    doc = get_object_or_404(DefenseDocument, pk=pk)

    # ایجاد یک فایل Word جدید
    document = Document()
    document.add_heading(doc.subject, level=1).alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT  # عنوان راست‌چین

    # تابع کمکی برای راست‌چین کردن متن
    def add_rtl_paragraph(doc, text, bold=False):
        paragraph = doc.add_paragraph()
        paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
        run = paragraph.add_run(text)
        run.bold = bold
        run.font.size = Pt(12)
        run.font.name = "Tahoma"  # فونت فارسی

        # تنظیم راست‌چین شدن در XML
        rtl = OxmlElement('w:rtl')
        run._r.get_or_add_rPr().append(rtl)

    # اضافه کردن جزئیات سند
    add_rtl_paragraph(document, f"مرحله: {doc.get_stage_display()}")
    add_rtl_paragraph(document, f"تاریخ ثبت: {doc.created_at.strftime('%Y/%m/%d')}")
    add_rtl_paragraph(document, "موضوع لایحه:", bold=True)

    # فیلد content وجود ندارد — از subject استفاده می‌شود
    # اگر فایل Word آپلود شده، لینک آن نمایش داده می‌شود
    summary_text = doc.subject or "متن لایحه ثبت نشده است."
    add_rtl_paragraph(document, summary_text)

    if doc.word_file:
        add_rtl_paragraph(document, f"فایل Word پیوست: {doc.word_file.name}")

    # ذخیره در حافظه و ارسال فایل به کاربر
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    filename = f"{doc.slug or 'document'}.docx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    document.save(response)

    return response

@login_required(login_url='/login/')
def convert_meeting_to_movakel(request, meeting_id):
    meeting = get_object_or_404(RequestMeeting, id=meeting_id)
    
    if meeting.status == "converted":
        messages.warning(request, "این درخواست قبلاً به وکالت تبدیل شده است.")
        return redirect("meeting_list")

    movakel = Movakel.objects.create(
        request_meeting=meeting,
        name=meeting.full_name,
        mobile_number=meeting.mobile_number,
        file_number=meeting.phone_number,
        #short_description="پرونده ایجاد شده از درخواست ملاقات",
        description="پرونده ایجاد شده از درخواست ملاقات",
        age="0",
        mechanized_number=str(uuid.uuid4())[:10],
        is_active=True,
    )
    # فرض کنید یک فیلد به نام `is_client` دارید که وضعیت موکل را نشان می‌دهد.
    #movakel.is_client = True
    meeting.status = "converted"
    meeting.save()

    messages.success(request, "✅ درخواست ملاقات با موفقیت به موکل تبدیل شد.")
    return redirect("movakel-detail", slug=movakel.slug)

def generate_pdf(request, meeting_id):
    meeting = RequestMeeting.objects.get(id=meeting_id)

     # 📌 تبدیل نام فارسی به UTF-8 برای دانلود صحیح
    safe_full_name = urllib.parse.quote(meeting.full_name.replace(" ", "_"))

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{safe_full_name}.pdf"'

    p = canvas.Canvas(response)
    p.setTitle("فرم پذیرش متقاضی")

    # ✅ مسیر کامل فونت ایران سنس
    font_path = os.path.join(settings.BASE_DIR, "static", "fonts", "IRANSans.ttf")
        # ✅ بررسی وجود فایل فونت
    if not os.path.exists(font_path):
        return HttpResponse("⚠️ خطا: فونت ایران سنس یافت نشد. لطفاً آن را در مسیر static/fonts/ قرار دهید.", status=500)

    # ✅ ثبت فونت در ReportLab
    pdfmetrics.registerFont(TTFont("IranSans", font_path))
    p.setFont("IranSans", 14)

    # 📌 نوشتن اطلاعات در PDF
    p.drawString(200, 800, "فرم پذیرش متقاضی")
    p.drawString(100, 770, f"نام و نام خانوادگی: {meeting.full_name}")
    p.drawString(100, 750, f"کد ملی: {meeting.national_id}")
    #p.drawString(100, 730, f"سال تولد: {meeting.birth_year}")
    birth_year = meeting.birth_date.year if meeting.birth_date else "-"
    p.drawString(100, 730, f"سال تولد: {birth_year}")
    p.drawString(100, 710, f"نشانی: {meeting.address or '-'}")
    p.drawString(100, 690, f"کد پستی: {meeting.postal_code or '-'}")
    p.drawString(100, 670, f"تلفن ثابت: {meeting.phone_number}")
    p.drawString(100, 650, f"ایمیل: {meeting.email or '-'}")

    p.showPage()
    p.save()

    return response

@login_required(login_url='/login/')
@user_passes_test(is_admin, login_url='/access-denied/')
def show_payment_details(request, movakel_id):
    try:
        # دریافت اطلاعات موکل
        movakel = get_object_or_404(Movakel, id=movakel_id)


        # دریافت هزینه‌های خدمات (اگر فیلدها None بودند، صفر در نظر گرفته می‌شود)
        service_type = getattr(movakel, 'service_type', None)
        service_type = ServiceType.objects.filter(movakel=movakel).first()
        def convert_to_decimal(value):
            """تبدیل مقدار به Decimal یا صفر اگر None باشد."""
            return Decimal(value) if value is not None else Decimal(0)
            
        selected_service_type = {
            'travel_fee': convert_to_decimal(getattr(service_type, 'travel_fee', None)),
            'miscellaneous_fee': convert_to_decimal(getattr(service_type, 'miscellaneous_fee', None)),
            'contract_fee': convert_to_decimal(getattr(service_type, 'contract_fee', None)),
            'bill_fee': convert_to_decimal(getattr(service_type, 'bill_fee', None)),
            'initial_fee': convert_to_decimal(getattr(service_type, 'initial_fee', None)),
            'appeal_fee': convert_to_decimal(getattr(service_type, 'appeal_fee', None)),
            'enforcement_fee': convert_to_decimal(getattr(service_type, 'enforcement_fee', None)),
            'petition_fee': convert_to_decimal(getattr(service_type, 'petition_fee', None)),
            'court_service_fee': convert_to_decimal(getattr(service_type, 'court_service_fee', None)),
            'notification_fee': convert_to_decimal(getattr(service_type, 'notification_fee', None)),
            'document_fee': convert_to_decimal(getattr(service_type, 'document_fee', None)),
        }
        selected_services = (
            service_type.get_selected_services()
            if service_type else []
        )
        # دریافت جزئیات پرداخت‌ها
        payment_details = PaymentDetail.objects.filter(movakel=movakel)

        # محاسبه مجموع هزینه‌های لوایح (اگر وجود نداشت، صفر شود)
        defense_documents = DefenseDocument.objects.filter(movakel=movakel)
        
        # محاسبه جمع کل هزینه‌های خدمات
        #total_service_fee = int(sum(selected_service_type.values()))
        total_service_fee = service_type.total_fee if service_type else Decimal(0)
        # محاسبه جمع کل پرداخت‌های انجام‌شده
        total_payment_detail_amount = Decimal(payment_details.aggregate(total_fee=Sum('amount'))['total_fee'] or 0)
        
        # محاسبه هزینه‌های جلسات
        meetings = RequestMeeting.objects.filter(movakel=movakel)
        meeting_fees = Decimal(meetings.aggregate(total_fee=Sum('meeting_fee'))['total_fee'] or Decimal(0))

        # تبدیل تاریخ‌ها به شمسی
        for meeting in meetings:
            meeting.meeting_date_shamsi = (
                jdatetime.datetime.fromgregorian(datetime=meeting.meeting_date).strftime('%Y/%m/%d') 
                if meeting.meeting_date else "-"
            )

        # محاسبه کل مبلغ قابل‌پرداخت
        total_amount = (
            total_service_fee + 
            total_payment_detail_amount + 
            meeting_fees
            )
        # محاسبه مالیات‌ها
        stamp_tax = total_amount * Decimal('0.05')  # تمبر مالیاتی ۵%
        judiciary_share = total_amount * Decimal('0.05')  # سهم قوه قضاییه ۵%
        annual_tax = total_amount * Decimal('0.25')  # مالیات پایان سال ۲۵%
        total_tax = stamp_tax + judiciary_share + annual_tax  # جمع کل مالیات‌ها

        # محاسبه مجموع پرداخت‌های حق الوکاله
        total_paid = movakel.installment_payments.filter(is_paid=True).aggregate(total=Sum('amount'))['total'] or 0
        
        # محاسبه باقی‌مانده بدهی
        remaining_amount = max(Decimal(0), Decimal(movakel.total_amount) - Decimal(total_paid))


        # محاسبه هزینه قرارداد
        contract_fee = Decimal(0)  # مقدار پیش‌فرض
        if hasattr(movakel, 'contract_payment') and movakel.contract_payment:
            contract_fee = Decimal(movakel.contract_payment.total_amount) if movakel.contract_payment.total_amount else Decimal(0)
        
        context = {
            'movakel': movakel,
            'meetings': meetings,
            'selected_service_type': selected_service_type,
            'selected_services': selected_services,
            'total_service_fee': total_service_fee,
            'contract_fee': contract_fee,
            'payment_details': payment_details,
            'meeting_fees': meeting_fees,
            'total_payment_detail_amount': total_payment_detail_amount,
            'defense_documents': defense_documents, 
            'total_amount': total_amount,
            'total_paid': total_paid,  # جمع کل پرداخت‌ها
            'remaining_amount': remaining_amount,  # مبلغ باقی‌مانده
            'stamp_tax': movakel.stamp_tax(),
            'judiciary_share': movakel.judiciary_share(),
            'annual_tax': movakel.annual_tax(),
            'total_tax': movakel.total_tax(),
        }

        return render(request, 'movakel_module/payment_details.html', context)

    except Movakel.DoesNotExist:
        return render(request, 'error_page.html', {'message': 'موکل پیدا نشد!'})


def categorized_movakels_view(request):
    # فرض کنید شما movakels را دسته‌بندی بر اساس سال دارید
    categorized_movakels = {}
    movakels = Movakel.objects.all()
    
    for movakel in movakels:
        # فرض بر اینکه شما از 'hearing_date' به عنوان معیار دسته‌بندی استفاده می‌کنید
        year = movakel.hearing_date.year  # سال میلادی

        # تبدیل سال میلادی به شمسی
        shamsi_year = jdatetime.date.fromgregorian(date=movakel.hearing_date).year

        if shamsi_year not in categorized_movakels:
            categorized_movakels[shamsi_year] = []

        categorized_movakels[shamsi_year].append(movakel)

    context = {'categorized_movakels': categorized_movakels}
    return render(request, 'movakel_module/movakel_list.html', context)

@login_required(login_url='/login/')
def hearing_calendar_view(request):
    today = date.today()

    # جلسات امروز
    today_hearings = Movakel.objects.filter(
        is_delete=False,
        hearing_date=today
    ).order_by('hearing_time')

    # جلسات آینده (۳۰ روز آینده)
    from datetime import timedelta
    upcoming_hearings = Movakel.objects.filter(
        is_delete=False,
        hearing_date__gt=today,
        hearing_date__lte=today + timedelta(days=30)
    ).order_by('hearing_date', 'hearing_time')

    # جلسات گذشته (۳۰ روز قبل)
    past_hearings = Movakel.objects.filter(
        is_delete=False,
        hearing_date__lt=today,
        hearing_date__gte=today - timedelta(days=30)
    ).order_by('-hearing_date')

    context = {
        'today': today,
        'today_hearings': today_hearings,
        'upcoming_hearings': upcoming_hearings,
        'past_hearings': past_hearings,
        'today_count': today_hearings.count(),
        'upcoming_count': upcoming_hearings.count(),
    }
    return render(request, 'movakel_module/hearing_calendar.html', context)


@login_required(login_url='/login/')
def add_installment(request, movakel_id):
    movakel = get_object_or_404(Movakel, id=movakel_id)
    if request.method == "POST":
        amount = Decimal(request.POST.get("amount"))
        
        # ثبت قسط جدید
        installment_payment = InstallmentPayment.objects.create(
            movakel=movakel, 
            amount=amount,
            due_date=date.today(),
            is_paid=True
        )
        
        # تاریخ شمسی
        due_date_shamsi = jalali_date.datetime2jalali(installment_payment.due_date).strftime('%Y/%m/%d')
        
        # محاسبه جمع کل پرداخت‌ها
        total_paid = movakel.installment_payments.filter(is_paid=True).aggregate(total=Sum('amount'))['total']
        if total_paid is None:
            total_paid = Decimal(0)
        
        # محاسبه مبلغ باقی‌مانده
        remaining_amount = max(Decimal(0), movakel.total_amount - total_paid)
        
        # ارسال داده‌ها به قالب
        context = {
            'movakel': movakel,
            'total_paid': total_paid,  # اضافه کردن جمع کل پرداخت‌ها به context
            'remaining_amount': remaining_amount,  # ارسال مبلغ باقی‌مانده
        }
        
        messages.success(request, f"پرداخت جدید با موفقیت ثبت شد.")
        return redirect("movakel-detail", slug=movakel.slug)
    
    # در صورت خطا
    messages.error(request, "درخواست نامعتبر است.")
    return redirect("movakel-detail", slug=movakel.slug)



@login_required(login_url='/login/')
def advanced_search_view(request):
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '')
    status = request.GET.get('status', '')  # active / inactive
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    movakels = Movakel.objects.filter(is_delete=False)

    # جستجوی متنی
    if query:
        movakels = movakels.filter(
            Q(name__icontains=query) |
            Q(mechanized_number__icontains=query) |
            Q(mobile_number__icontains=query) |
            Q(file_number__icontains=query) |
            Q(description__icontains=query)
        )

    # فیلتر دسته‌بندی
    if category_id:
        movakels = movakels.filter(category_id=category_id)

    # فیلتر وضعیت
    if status == 'active':
        movakels = movakels.filter(is_active=True)
    elif status == 'inactive':
        movakels = movakels.filter(is_active=False)

    # فیلتر تاریخ وکالت
    if date_from:
        movakels = movakels.filter(contract_date__gte=date_from)
    if date_to:
        movakels = movakels.filter(contract_date__lte=date_to)

    categories = MovakelCategory.objects.all()

    context = {
        'movakels': movakels.order_by('-id'),
        'categories': categories,
        'query': query,
        'selected_category': category_id,
        'selected_status': status,
        'date_from': date_from,
        'date_to': date_to,
        'result_count': movakels.count(),
    }
    return render(request, 'movakel_module/advanced_search.html', context)



def update_case_status(request, movakel_id):
    movakel = get_object_or_404(Movakel, id=movakel_id, is_delete=False)
    if request.method == 'POST':
        new_status = request.POST.get('case_status')
        valid_statuses = ['in_progress', 'appeal', 'execution', 'closed', 'archived']
        if new_status in valid_statuses:
            movakel.case_status = new_status
            movakel.save()
            messages.success(request, f'✅ وضعیت پرونده به «{movakel.get_case_status_display()}» تغییر یافت.')
        else:
            messages.error(request, '❌ وضعیت نامعتبر است.')
    return redirect('movakel-detail', slug=movakel.slug)


@login_required
def backup_view(request):
    message = None
    error = None

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create':
            backup_path, result = create_backup()
            if backup_path:
                message = f'✅ فایل پشتیبان «{result}» با موفقیت ایجاد شد.'
            else:
                error = f'❌ خطا: {result}'

        elif action == 'delete':
            filename = request.POST.get('filename', '')
            if delete_backup(filename):
                message = f'✅ فایل «{filename}» حذف شد.'
            else:
                error = '❌ فایل یافت نشد یا خطایی رخ داد.'

    backups = get_all_backups()
    context = {
        'backups': backups,
        'message': message,
        'error': error,
    }
    return render(request, 'movakel_module/backup.html', context)


@login_required
def download_backup(request, filename):
    import os
    from django.conf import settings
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    file_path = os.path.join(backup_dir, filename)

    if os.path.exists(file_path) and filename.endswith('.sqlite3'):
        response = FileResponse(open(file_path, 'rb'), as_attachment=True, filename=filename)
        return response

    messages.error(request, '❌ فایل یافت نشد.')
    return redirect('backup_view')



@login_required
def print_contract(request, movakel_id):
    movakel = get_object_or_404(Movakel, id=movakel_id, is_delete=False)

    # تنظیم فونت فارسی
    font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'IRANSans.ttf')
    pdfmetrics.registerFont(TTFont('IRANSans', font_path))

    response = HttpResponse(content_type='application/pdf')
    safe_name = urllib.parse.quote(movakel.name.replace(' ', '_'))
    response['Content-Disposition'] = f'attachment; filename="contract_{safe_name}.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    p.setFont('IRANSans', 14)

    def draw_rtl(text, y, size=12, bold=False):
        p.setFont('IRANSans', size)
        text = str(text) if text else "-"
        if BIDI_AVAILABLE:
            reshaped = arabic_reshaper.reshape(text)
            display_text = get_display(reshaped)
        else:
            display_text = text
        p.drawRightString(width - 50, y, display_text)

    # عنوان
    draw_rtl('قرارداد وکالت', height - 60, size=18)

    # خط جداکننده
    p.line(50, height - 75, width - 50, height - 75)

    # مشخصات موکل
    draw_rtl('مشخصات موکل', height - 110, size=14)
    draw_rtl(f'نام و نام خانوادگی: {movakel.name}', height - 140)
    draw_rtl(f'شماره تماس: {movakel.mobile_number}', height - 165)
    draw_rtl(f'شماره پرونده مکانیزه: {movakel.mechanized_number or "-"}', height - 190)
    draw_rtl(f'تاریخ وکالت: {movakel.contract_date or "-"}', height - 215)
    draw_rtl(f'دسته‌بندی: {movakel.category or "-"}', height - 240)

    # خط جداکننده
    p.line(50, height - 255, width - 50, height - 255)

    # مشخصات مالی
    draw_rtl('مشخصات مالی', height - 285, size=14)
    draw_rtl(f'مبلغ کل حق‌الوکاله: {movakel.total_amount:,} تومان', height - 315)
    draw_rtl(f'نحوه پرداخت: {movakel.get_payment_method_display() if movakel.payment_method else "-"}', height - 340)

    # خط جداکننده
    p.line(50, height - 355, width - 50, height - 355)

    # توضیحات پرونده
    draw_rtl('موضوع وکالت', height - 385, size=14)
    draw_rtl(movakel.description[:100] if movakel.description else '-', height - 415, size=11)

    # خط جداکننده
    p.line(50, height - 430, width - 50, height - 430)

    # امضا
    draw_rtl('امضای موکل', height - 530, size=11)
    draw_rtl('امضای وکیل', height - 530, size=11)
    p.line(50, height - 510, 200, height - 510)
    p.line(width - 200, height - 510, width - 50, height - 510)

    # footer
    draw_rtl('این قرارداد با استفاده از سامانه وکیل‌یار تنظیم شده است.', 40, size=9)

    p.showPage()
    p.save()
    return response
# ============================================================
# ویرایش مستقیم رکوردهای نمایش داده شده در صفحه جزئیات موکل
# ============================================================

@login_required(login_url='/login/')
def edit_request_meeting(request, pk):
    meeting = get_object_or_404(RequestMeeting, pk=pk)
    if request.method == 'POST':
        form = RequestMeetingEditForm(request.POST, instance=meeting)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ اطلاعات ملاقات با موفقیت ویرایش شد.')
            if meeting.movakel_id:
                return redirect('movakel-detail', slug=meeting.movakel.slug)
            return redirect('meeting_list')
    else:
        form = RequestMeetingEditForm(instance=meeting)
    return render(request, 'movakel_module/related_edit.html', {
        'form': form,
        'title': 'ویرایش اطلاعات ملاقات',
        'subtitle': meeting.full_name,
        'back_url': meeting.movakel.get_absolute_url() if meeting.movakel else None,
    })


@login_required(login_url='/login/')
def edit_visit(request, pk):
    visit = get_object_or_404(Visit, pk=pk)
    if request.method == 'POST':
        form = VisitEditForm(request.POST, instance=visit)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ اطلاعات مراجعه با موفقیت ویرایش شد.')
            return redirect('movakel-detail', slug=visit.movakel.slug)
    else:
        form = VisitEditForm(instance=visit)
    return render(request, 'movakel_module/related_edit.html', {
        'form': form,
        'title': 'ویرایش مراجعه موکل به دفتر',
        'subtitle': visit.movakel.name,
        'back_url': visit.movakel.get_absolute_url(),
    })


@login_required(login_url='/login/')
def edit_service_type(request, pk):
    service_type = get_object_or_404(ServiceType, pk=pk)
    if request.method == 'POST':
        form = ServiceTypeForm(request.POST, instance=service_type)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ اطلاعات خدمات با موفقیت ویرایش شد.')
            return redirect('movakel-detail', slug=service_type.movakel.slug)
    else:
        form = ServiceTypeForm(instance=service_type)
    return render(request, 'movakel_module/related_edit.html', {
        'form': form,
        'title': 'ویرایش کامل خدمات و اقدامات',
        'subtitle': service_type.movakel.name,
        'back_url': service_type.movakel.get_absolute_url(),
    })


@login_required(login_url='/login/')
def edit_defense_document(request, pk):
    doc = get_object_or_404(DefenseDocument, pk=pk)
    if request.method == 'POST':
        form = DefenseDocumentEditForm(request.POST, request.FILES, instance=doc)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ لایحه با موفقیت ویرایش شد.')
            return redirect('movakel-detail', slug=doc.movakel.slug)
    else:
        form = DefenseDocumentEditForm(instance=doc)
    return render(request, 'movakel_module/related_edit.html', {
        'form': form,
        'title': 'ویرایش لایحه',
        'subtitle': doc.movakel.name,
        'back_url': doc.movakel.get_absolute_url(),
    })


@login_required(login_url='/login/')
def edit_pdf_file(request, pk):
    pdf = get_object_or_404(PDFFile, pk=pk)
    if request.method == 'POST':
        form = PDFFileEditForm(request.POST, request.FILES, instance=pdf)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ فایل PDF با موفقیت ویرایش شد.')
            movakel = pdf.movakels.filter(is_delete=False).first()
            if movakel:
                return redirect('movakel-detail', slug=movakel.slug)
            return redirect('movakel-list')
    else:
        form = PDFFileEditForm(instance=pdf)
    movakel = pdf.movakels.filter(is_delete=False).first()
    return render(request, 'movakel_module/related_edit.html', {
        'form': form,
        'title': 'ویرایش فایل PDF',
        'subtitle': pdf.name,
        'back_url': movakel.get_absolute_url() if movakel else None,
    })


@login_required(login_url='/login/')
def edit_movakel_basic(request, slug):
    movakel = get_object_or_404(Movakel, slug=slug, is_delete=False)
    if request.method == 'POST':
        form = MovakelBasicEditForm(request.POST, request.FILES, instance=movakel)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ اطلاعات اصلی موکل با موفقیت ویرایش شد.')
            return redirect('movakel-detail', slug=movakel.slug)
    else:
        form = MovakelBasicEditForm(instance=movakel)
    return render(request, 'movakel_module/related_edit.html', {
        'form': form,
        'title': 'ویرایش اطلاعات اصلی موکل',
        'subtitle': movakel.name,
        'back_url': movakel.get_absolute_url(),
    })


@login_required(login_url='/login/')
def edit_court_info(request, slug):
    movakel = get_object_or_404(Movakel, slug=slug, is_delete=False)
    if request.method == 'POST':
        form = CourtInfoEditForm(request.POST, instance=movakel)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ اطلاعات پرونده و دادگاه با موفقیت ویرایش شد.')
            return redirect('movakel-detail', slug=movakel.slug)
    else:
        form = CourtInfoEditForm(instance=movakel)
    return render(request, 'movakel_module/related_edit.html', {
        'form': form,
        'title': 'ویرایش اطلاعات پرونده و دادگاه',
        'subtitle': movakel.name,
        'back_url': movakel.get_absolute_url(),
    })


@login_required(login_url='/login/')
def edit_movakel_notes(request, slug):
    movakel = get_object_or_404(Movakel, slug=slug, is_delete=False)
    if request.method == 'POST':
        form = MovakelNotesEditForm(request.POST, instance=movakel)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ ملاحظات پرونده با موفقیت ویرایش شد.')
            return redirect('movakel-detail', slug=movakel.slug)
    else:
        form = MovakelNotesEditForm(instance=movakel)
    return render(request, 'movakel_module/related_edit.html', {
        'form': form,
        'title': 'ویرایش ملاحظات پرونده',
        'subtitle': movakel.name,
        'back_url': movakel.get_absolute_url(),
    })



def edit_meeting_ajax(request, meeting_id):
    """نمایش فرم ویرایش ملاقات‌کننده به‌صورت Ajax"""
    meeting = get_object_or_404(Meeting, id=meeting_id)
    
    if request.method == 'POST':
        form = MeetingForm(request.POST, instance=meeting)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'message': 'اطلاعات با موفقیت ذخیره شد'})
        else:
            html = render_to_string('includes/meeting_edit_form.html', {
                'form': form,
                'meeting': meeting
            }, request=request)
            return HttpResponse(html)
    
    form = MeetingForm(instance=meeting)
    html = render_to_string('includes/meeting_edit_form.html', {
        'form': form,
        'meeting': meeting
    }, request=request)
    return HttpResponse(html)



def site_header_component(request):
    setting: SiteSetting = SiteSetting.objects.filter(is_main_setting=True).first()
    context = {
        'site_setting': setting
    }
    return render(request, 'shared/site_header_component.html', context)


def site_footer_component(request):
    setting: SiteSetting = SiteSetting.objects.filter(is_main_setting=True).first()
    # FooterLinkBox در migration حذف شده — به صورت امن handle می‌شود
    try:
        from site_module.models import FooterLinkBox
        footer_link_boxes = FooterLinkBox.objects.all()
    except (ImportError, Exception):
        footer_link_boxes = []
    context = {
        'site_setting': setting,
        'footer_link_boxes': footer_link_boxes
    }
    return render(request, 'shared/site_footer_component.html', context)
