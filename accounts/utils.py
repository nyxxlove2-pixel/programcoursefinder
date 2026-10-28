from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from .models import User

SESSION_KEY = 'user_id'


def log_in(request, user):
    # Remember who is logged in by saving their id in the session
    request.session.cycle_key()
    request.session[SESSION_KEY] = user.id


def log_out(request):
    request.session.flush()


def get_current_user(request):
    """Return the logged-in User, or None if nobody is logged in."""
    user_id = request.session.get(SESSION_KEY)
    if user_id is None:
        return None
    return User.objects.filter(id=user_id).first()


def redirect_home(user):
    """Send each role to its own start page: users browse courses, organizations see their dashboard."""
    if user.is_organization:
        return redirect('organizations:dashboard')
    return redirect('courses:search')


def role_required(role=None):
    """Only let logged-in users in. If a role is given, only that role.

    Usage:  @role_required()                 any logged-in account
            @role_required('organization')   organization accounts only
    The logged-in user is available in the view as request.app_user.
    """
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            user = get_current_user(request)
            if user is None:
                messages.info(request, 'Please log in first.')
                return redirect('accounts:login')
            if role and user.role != role:
                messages.error(request, 'You do not have access to that page.')
                return redirect('core:home')
            request.app_user = user
            return view(request, *args, **kwargs)
        return wrapper
    return decorator
