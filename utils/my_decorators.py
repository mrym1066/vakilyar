import logging
from django.http import HttpRequest
from django.shortcuts import redirect
from django.urls import reverse

logger = logging.getLogger(__name__)


def permission_checker_decorator_factory(data=None):
    """
    Decorator factory برای کنترل دسترسی — فقط superuser مجاز است.
    data: دیکشنری شامل 'permission_name' برای logging
    """
    def permission_checker_decorator(func):
        def wrapper(request: HttpRequest, *args, **kwargs):
            permission_name = data.get('permission_name', 'unknown') if data else 'unknown'
            if request.user.is_authenticated and request.user.is_superuser:
                logger.debug(f"Admin access granted: {permission_name} by {request.user.username}")
                return func(request, *args, **kwargs)
            else:
                logger.warning(
                    f"Unauthorized admin access attempt: {permission_name} "
                    f"by user={getattr(request.user, 'username', 'anonymous')}"
                )
                return redirect(reverse('login_page'))
        return wrapper
    return permission_checker_decorator
