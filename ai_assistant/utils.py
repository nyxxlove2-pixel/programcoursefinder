from django.conf import settings
from django.core.cache import cache

ONE_HOUR = 60 * 60
BUSY_MESSAGE = 'The AI is not available right now. Please try again in a minute.'


def take_ai_request(user):
    """Count one AI request for this account.
    Returns False (and counts nothing) once they reach the hourly limit."""
    key = f'ai-requests-{user.id}'
    cache.add(key, 0, timeout=ONE_HOUR)  # starts the hour on the first request
    if cache.get(key, 0) >= settings.AI_REQUESTS_PER_HOUR:
        return False
    cache.incr(key)
    return True


def limit_message():
    return f'You can make {settings.AI_REQUESTS_PER_HOUR} AI requests per hour. Please try again later.'
