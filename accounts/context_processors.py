from notifications.utils import unread_count

from .utils import get_current_user


def current_user(request):
    # Makes {{ current_user }}, {{ base_layout }} and {{ unread_notifications }} available in every template
    user = get_current_user(request)
    # Organizations get the sidebar layout on shared pages (like layouts/form_page.html)
    if user and user.is_organization:
        base_layout = 'layouts/organization.html'
    else:
        base_layout = 'base.html'
    return {
        'current_user': user,
        'base_layout': base_layout,
        'unread_notifications': unread_count(user) if user else 0,
    }
