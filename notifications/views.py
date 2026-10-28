from django.shortcuts import render

from accounts.utils import role_required


@role_required()
def notification_list(request):
    notifications = list(request.app_user.notifications.all()[:50])
    # Opening the page counts as reading them. The list above keeps the
    # old is_read values, so new ones are still highlighted this one time.
    request.app_user.notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'notifications/list.html', {'notifications': notifications})
