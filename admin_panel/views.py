from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required


# utils/my_decorators.py در پروژه وجود نداشت و ImportError می‌داد.
# جایگزین شد با staff_member_required استاندارد Django که همان کار را می‌کند:
# فقط کاربران is_staff=True می‌توانند وارد شوند، بقیه به /login/ redirect می‌شوند.
@staff_member_required(login_url='/login/')
def index(request):
    return render(request, 'admin_panel/home/index.html')
