from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from . import views


urlpatterns = [
    path('', RedirectView.as_view(url='login/'), name='home'),
    path('register/', views.RegisterView.as_view(), name='register_page'),
    path('login/', views.LoginView.as_view(), name='login_page'),
    path('logout/', views.LogoutView.as_view(), name='logout_page'),
    path('waiting-approval/', views.WaitingApprovalView.as_view(), name='waiting_approval_page'),

    # فراموشی رمز عبور — با ویوهای امن و استاندارد خود Django (توکن یک‌بارمصرف
    # امضاشده، نه فیلد دستی email_active_code که قبلاً حذف شده بود).
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='account_module/forgot_password.html',
            email_template_name='account_module/password_reset_email.html',
            subject_template_name='account_module/password_reset_subject.txt',
            success_url=reverse_lazy('password_reset_done_page'),
        ),
        name='password_reset_page',
    ),
    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='account_module/password_reset_done.html',
        ),
        name='password_reset_done_page',
    ),
    path(
        'password-reset-confirm/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='account_module/reset_password.html',
            success_url=reverse_lazy('password_reset_complete_page'),
        ),
        name='password_reset_confirm_page',
    ),
    path(
        'password-reset-complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='account_module/password_reset_complete.html',
        ),
        name='password_reset_complete_page',
    ),
]
