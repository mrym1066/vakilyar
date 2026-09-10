from django.views.generic import ListView
from site_module.models import SiteSetting
#from .forms import ContactUsModelForm
from django.views.generic.edit import CreateView
from .forms import ContactUsForm
from .models import ContactUs


class ContactUsView(CreateView):
    form_class = ContactUsForm
    template_name = 'contact_module/contact_us_page.html'  # اسم قالبت
    success_url = '/contact-us/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        setting = SiteSetting.objects.filter(is_main_setting=True).first()
        context['site_setting'] = setting
        return context