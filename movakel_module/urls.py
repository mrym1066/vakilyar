from django.urls import path, register_converter
from django.shortcuts import render
from . import views
from .views import (
    get_service_price, defense_document_detail, meeting_list_view,
    request_meeting_view, generate_pdf, download_document_word, service_type_detail
)


# مبدل اسلاگ فارسی
class UnicodeSlugConverter:
    regex = r'[\w\u0600-\u06FF-]+'

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value


register_converter(UnicodeSlugConverter, 'uslug')


urlpatterns = [
    path('', views.MovakelListView.as_view(), name='movakel-list'),
    path('cat/<cat>', views.MovakelListView.as_view(), name='movakel-categories-list'),

    # ===== گزارش مالی (مهم: قبل از slug) =====
    path('total-costs/', views.total_costs_view, name='total_costs'),

    # جلسات
    path('request-meeting/', request_meeting_view, name='request_meeting'),
    path('meetings/', meeting_list_view, name='meeting_list'),
    path('generate-pdf/<int:meeting_id>/', views.generate_pdf, name='meeting_pdf'),

    # ویرایش رکوردهای موجود
    path('edit/<uslug:slug>/', views.edit_movakel, name='edit_movakel'),
    path('edit/<uslug:slug>/court/', views.edit_court_info, name='edit_court_info'),
    path('edit/<uslug:slug>/notes/', views.edit_movakel_notes, name='edit_movakel_notes'),
    path('edit/meeting/<int:pk>/', views.edit_request_meeting, name='edit_request_meeting'),
    path('edit/visit/<int:pk>/', views.edit_visit, name='edit_visit'),
    path('edit/service/<int:pk>/', views.service_type_detail, name='service_type_detail'),
    path('edit/defense-document/<int:pk>/', views.edit_defense_document, name='edit_defense_document'),
    path('edit/pdf/<int:pk>/', views.edit_pdf_file, name='edit_pdf_file'),

    # پرداخت
    path('movakel/<int:movakel_id>/payment_details/', views.show_payment_details, name='payment_details'),

    # ابزارها
    path('calculate-damage/', views.calculate_damage_view, name='calculate_damage'),
    path('hearing-calendar/', views.hearing_calendar_view, name='hearing_calendar'),
    path('search/', views.advanced_search_view, name='advanced_search'),
    path('backup/', views.backup_view, name='backup_view'),
    path('backup/download/<str:filename>/', views.download_backup, name='download_backup'),
    path('print-contract/<int:movakel_id>/', views.print_contract, name='print_contract'),
    path('update-status/<int:movakel_id>/', views.update_case_status, name='update_case_status'),

    # اقدامات / خدمات
    path('update-services/<int:movakel_id>/', views.update_services, name='update_services'),
    path('service_type/<int:service_type_id>/', service_type_detail, name='service_type_detail'),
    path('service-type/<int:pk>/edit/', views.service_type_edit, name='service_type_edit'),

    # لایحه دفاعی
    path('defense-document/<int:pk>/', views.defense_document_detail, name='defense_document_detail'),
    path('defense-document/<int:pk>/download-word/', views.download_document_word, name='download_document_word'),

    # admin ajax
    path('admin/get_service_price/<int:service_type_id>/', get_service_price, name='get_service_price'),
    path('access-denied/', lambda request: render(request, 'errors/access_denied.html'), name='access_denied'),

    # ═══ PDF Generation ═══
    path('pdf/contract/<int:movakel_id>/', views.pdf_contract, name='pdf_contract'),
    path('pdf/report/<int:movakel_id>/', views.pdf_report, name='pdf_report'),
    path('pdf/total-report/', views.pdf_total_report, name='pdf_total_report'),
    path('pdf/meeting/<int:meeting_id>/', views.pdf_meeting_form, name='pdf_meeting_form'),
  
  
    # ===== این باید همیشه آخرین خط باشه =====
    path('<uslug:slug>/', views.MovakelDetailView.as_view(), name='movakel-detail'),
]