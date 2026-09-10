from django.http import HttpRequest
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from utils.my_decorators import permission_checker_decorator_factory


@login_required(login_url='/login/')
@permission_checker_decorator_factory({'permission_name': 'admin_index'})
def index(request: HttpRequest):
    return render(request, 'admin_panel/home/index.html')
