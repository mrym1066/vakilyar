from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from .models import User
from django.contrib.auth import login, logout
from article_module.models import Article

from account_module.forms import RegisterForm, LoginForm


class RegisterView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect(reverse('user_panel_dashboard'))
        register_form = RegisterForm()
        context = {'register_form': register_form}
        return render(request, 'account_module/register.html', context)

    def post(self, request):
        register_form = RegisterForm(request.POST)
        if register_form.is_valid():
            username = register_form.cleaned_data.get('username')
            email = register_form.cleaned_data.get('email')
            password = register_form.cleaned_data.get('password')
            user = User.objects.filter(username__iexact=username).exists()
            if user:
                register_form.add_error('username', 'نام کاربری وارد شده تکراری می‌باشد')
            else:
                # حساب با is_active=False و is_approved=False ساخته می‌شه.
                # ادمین باید از پنل هر دو فیلد رو True کنه تا کاربر بتونه لاگین کنه.
                new_user = User(username=username, email=email, is_active=False, is_approved=False)
                new_user.set_password(password)
                new_user.save()
                return redirect(reverse('waiting_approval_page'))

        context = {'register_form': register_form}
        return render(request, 'account_module/register.html', context)


class LoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect(reverse('user_panel_dashboard'))
        login_form = LoginForm()
        context = {'login_form': login_form}
        return render(request, 'account_module/login.html', context)

    def post(self, request):
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            username = login_form.cleaned_data.get('username')
            password = login_form.cleaned_data.get('password')
            user = User.objects.filter(username__iexact=username).first()
            generic_error = 'نام کاربری یا کلمه عبور اشتباه است'

            if user is not None:
                password_is_correct = user.check_password(password)
            else:
                # حتی وقتی کاربر وجود ندارد، یک هش محاسبه می‌کنیم تا زمان پاسخ با حالت
                # «کاربر موجود ولی رمز غلط» یکسان بماند (جلوگیری از افشای وجود
                # نام‌کاربری از طریق تفاوت زمانی پاسخ - timing attack).
                User().set_password(password)
                password_is_correct = False

            # نکته امنیتی: بررسی is_active/is_approved باید *بعد* از تأیید صحت رمز
            # عبور انجام شود، وگرنه یک مهاجم می‌تواند با هر رمز دلخواه، صرفاً با آزمایش
            # نام‌های کاربری مختلف، وجود/وضعیت یک حساب را کشف کند (User Enumeration).
            if not password_is_correct:
                login_form.add_error(None, generic_error)
            elif not user.is_active:
                login_form.add_error(None, 'حساب کاربری شما هنوز فعال نشده است')
            elif not user.is_approved:
                login_form.add_error(None, 'حساب کاربری شما در انتظار تأیید مدیر سیستم است')
            else:
                login(request, user)
                return redirect(reverse('user_panel_dashboard'))

        context = {'login_form': login_form}
        return render(request, 'account_module/login.html', context)


class LogoutView(View):
    def get(self, request):
        # نکته: بهتر است لینک خروج در تمپلیت (که در این بررسی حضور نداشت) به یک
        # دکمه/فرم POST تبدیل شود؛ چون GET برای اکشن‌های تغییردهنده‌ی وضعیت (مثل
        # خروج از حساب) ایمن نیست (مثلاً می‌توان با یک لینک/تصویر مخرب کاربر را
        # به‌صورت ناخواسته خارج کرد). فعلاً هم GET و هم POST پشتیبانی می‌شود تا
        # لینک فعلی در سایت خراب نشود.
        logout(request)
        return redirect(reverse('login_page'))

    def post(self, request):
        return self.get(request)


class WaitingApprovalView(View):
    def get(self, request):
        articles = Article.objects.order_by('-id')[:6]
        return render(request, 'account_module/waiting_approval.html', {'articles': articles})
