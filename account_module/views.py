from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from .models import User
from django.utils.crypto import get_random_string
from django.http import Http404, HttpRequest
from django.contrib.auth import login, logout
from utils.email_service import send_email
from article_module.models import Article

from account_module.forms import RegisterForm, LoginForm, ForgotPasswordForm, ResetPasswordForm


class RegisterView(View):
    def get(self, request):
        register_form = RegisterForm()
        context = {'register_form': register_form}
        return render(request, 'account_module/register.html', context)

    def post(self, request):
        register_form = RegisterForm(request.POST)
        if register_form.is_valid():
            username = register_form.cleaned_data.get('username')
            password = register_form.cleaned_data.get('password')
            user = User.objects.filter(username__iexact=username).exists()
            if user:
                register_form.add_error('username', 'نام کاربری وارد شده تکراری می‌باشد')
            else:
                # حساب با is_active=False و is_approved=False ساخته می‌شه.
                # ادمین باید از پنل هر دو فیلد رو True کنه تا کاربر بتونه لاگین کنه.
                new_user = User(username=username, is_active=False, is_approved=False)
                new_user.set_password(password)
                new_user.save()
                return redirect(reverse('waiting_approval_page'))

        context = {'register_form': register_form}
        return render(request, 'account_module/register.html', context)


class ActivateAccountView(View):
    """
    این ویو برای فعال‌سازی از طریق لینک ایمیل بود.
    چون پروژه آفلاینه و ایمیل ارسال نمی‌شه، این مسیر استفاده نمی‌شه.
    فعال‌سازی حساب از طریق پنل ادمین (is_active + is_approved) انجام می‌گیره.
    """
    def get(self, request, email_active_code):
        user: User = User.objects.filter(email_active_code__iexact=email_active_code).first()
        if user is not None:
            if not user.is_active:
                user.is_active = True
                user.email_active_code = get_random_string(72)
                user.save()
                return redirect(reverse('login_page'))
            else:
                pass

        raise Http404


class LoginView(View):
    def get(self, request):
        login_form = LoginForm()
        context = {'login_form': login_form}
        return render(request, 'account_module/login.html', context)

    def post(self, request):
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            username = login_form.cleaned_data.get('username')
            password = login_form.cleaned_data.get('password')
            user = User.objects.filter(username__iexact=username).first()
            if user is not None:
                if not user.is_active:
                    login_form.add_error('username', 'حساب کاربری شما هنوز فعال نشده است')
                elif not user.is_approved:
                    login_form.add_error('username', 'حساب کاربری شما در انتظار تأیید مدیر سیستم است')
                else:
                    is_password_correct = user.check_password(password)
                    if is_password_correct:
                        login(request, user)
                        return redirect(reverse('user_panel_dashboard'))
                    else:
                        login_form.add_error('username', 'کلمه عبور اشتباه است')
            else:
                login_form.add_error('username', 'کاربری با مشخصات وارد شده یافت نشد')

        context = {'login_form': login_form}
        return render(request, 'account_module/login.html', context)


class ForgetPasswordView(View):
    def get(self, request: HttpRequest):
        forget_pass_form = ForgotPasswordForm()
        context = {'forget_pass_form': forget_pass_form}
        return render(request, 'account_module/forgot_password.html', context)

    def post(self, request: HttpRequest):
        forget_pass_form = ForgotPasswordForm(request.POST)
        if forget_pass_form.is_valid():
            username = forget_pass_form.cleaned_data.get('username')
            user = User.objects.filter(username__iexact=username).first()
            if user is not None:
                send_email('بازیابی کلمه عبور', user.email, {'user': user}, 'emails/forgot_password.html')
                return redirect(reverse('login_page'))

        context = {'forget_pass_form': forget_pass_form}
        return render(request, 'account_module/forgot_password.html', context)


class ResetPasswordView(View):
    def get(self, request: HttpRequest, active_code):
        user: User = User.objects.filter(email_active_code__iexact=active_code).first()
        if user is None:
            return redirect(reverse('login_page'))

        reset_pass_form = ResetPasswordForm()

        context = {
            'reset_pass_form': reset_pass_form,
            'user': user
        }
        return render(request, 'account_module/reset_password.html', context)

    def post(self, request: HttpRequest, active_code):
        reset_pass_form = ResetPasswordForm(request.POST)
        user: User = User.objects.filter(email_active_code__iexact=active_code).first()
        if reset_pass_form.is_valid():
            if user is None:
                return redirect(reverse('login_page'))
            user_new_pass = reset_pass_form.cleaned_data.get('password')
            user.set_password(user_new_pass)
            user.email_active_code = get_random_string(72)
            user.is_active = True
            user.save()
            return redirect(reverse('login_page'))

        context = {
            'reset_pass_form': reset_pass_form,
            'user': user
        }

        return render(request, 'account_module/reset_password.html', context)


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect(reverse('login_page'))


class WaitingApprovalView(View):
    def get(self, request):
        articles = Article.objects.order_by('-id')[:6]
        return render(request, 'account_module/waiting_approval.html', {'articles': articles})
