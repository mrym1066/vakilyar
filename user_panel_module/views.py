from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth.mixins import AccessMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.utils import timezone
from django.db.models import Sum

from .forms import EditProfileModelForm, ChangePasswordForm
from movakel_module.models import Movakel, RequestMeeting, MovakelPayment


# ── Mixin: فقط کاربران تأییدشده یا staff اجازه دسترسی دارند ──
class ApprovedUserMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login_page')
        if not request.user.is_approved and not request.user.is_staff:
            return render(request, 'account_module/waiting_approval.html')
        return super().dispatch(request, *args, **kwargs)


# ---------------- DASHBOARD ----------------
class UserPanelDashboardPage(ApprovedUserMixin, TemplateView):
    template_name = 'user_panel_module/user_panel_dashboard_page.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()

        all_movakels = Movakel.objects.all()
        context['total_movakels']    = all_movakels.count()
        context['active_movakels']   = all_movakels.filter(is_active=True).count()
        context['inactive_movakels'] = all_movakels.filter(is_active=False).count()

        context['pending_meetings'] = RequestMeeting.objects.filter(
            status='pending'
        ).count()

        total = MovakelPayment.objects.filter(
            is_delete=False
        ).aggregate(s=Sum('amount'))['s'] or 0
        context['total_income'] = int(total)

        monthly = MovakelPayment.objects.filter(
            is_delete=False,
            payment_date__year=today.year,
            payment_date__month=today.month,
        ).aggregate(s=Sum('amount'))['s'] or 0
        context['monthly_income'] = int(monthly)

        today_list = all_movakels.filter(hearing_date=today).select_related()
        context['today_hearing_list'] = today_list
        context['today_hearings']     = today_list.count()

        week_end = today + timezone.timedelta(days=7)
        context['week_hearings'] = all_movakels.filter(
            hearing_date__gte=today,
            hearing_date__lte=week_end,
        ).order_by('hearing_date')

        context['latest_movakels'] = all_movakels.order_by('-id')[:10]
        context['today'] = today

        return context


# ---------------- EDIT PROFILE ----------------
class EditUserProfilePage(ApprovedUserMixin, View):
    template_name = 'user_panel_module/edit_profile_page.html'

    def get(self, request):
        form = EditProfileModelForm(instance=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = EditProfileModelForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('user_panel_dashboard')
        return render(request, self.template_name, {'form': form})


# ---------------- CHANGE PASSWORD ----------------
class ChangePasswordPage(ApprovedUserMixin, View):
    template_name = 'user_panel_module/change_password_page.html'

    def get(self, request):
        form = ChangePasswordForm(user=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = ChangePasswordForm(request.POST, user=request.user)
        if form.is_valid():
            user = request.user
            # باگ قبلی: if user.check_password(...): ... form.add_error(...)
            # یعنی اگر رمز اشتباه بود، add_error فراخوانی می‌شد ولی
            # return نداشت و فرم بدون پیام خطا دوباره رندر می‌شد.
            if not user.check_password(form.cleaned_data['current_password']):
                form.add_error('current_password', 'کلمه عبور فعلی اشتباه است')
                return render(request, self.template_name, {'form': form})
            user.set_password(form.cleaned_data['password'])
            user.save()
            # update_session_auth_hash جلوگیری از logout شدن بعد از تغییر رمز
            update_session_auth_hash(request, user)
            return redirect('user_panel_dashboard')
        return render(request, self.template_name, {'form': form})


@login_required
def user_panel_menu_component(request):
    return render(request, 'user_panel_module/components/user_panel_menu_component.html')
