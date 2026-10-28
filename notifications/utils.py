from .models import Notification


def notify(user, message, link=''):
    """Send one notification to an account. Every app uses this to notify someone."""
    Notification.objects.create(user=user, message=message, link=link)


def unread_count(user):
    return Notification.objects.filter(user=user, is_read=False).count()
