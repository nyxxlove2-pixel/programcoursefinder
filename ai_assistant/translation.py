import hashlib

from django.core.cache import cache

from .groq import ask_groq

SESSION_KEY = 'translated_reviews'  # review ids this visitor asked to see in English
ONE_WEEK = 60 * 60 * 24 * 7

SYSTEM_PROMPT = """Translate the student's review into natural English.
If it is already in English, return it unchanged.
Reply with the translation only, no notes."""


def cache_key(text):
    # The same comment always gives the same key, so each text is translated only once
    return 'translation-' + hashlib.sha256(text.encode()).hexdigest()


def cached_translation(text):
    return cache.get(cache_key(text))


def translate(text):
    """English version of the text, from the cache when we already translated it."""
    translation = cached_translation(text)
    if translation is None:
        translation = ask_groq(SYSTEM_PROMPT, text, max_tokens=1000)
        cache.set(cache_key(text), translation, timeout=ONE_WEEK)
    return translation


def remember_translated(request, review_id):
    ids = request.session.get(SESSION_KEY, [])
    if review_id not in ids:
        request.session[SESSION_KEY] = ids + [review_id]


def attach_translations(reviews, request):
    """Set review.translation on the reviews this visitor chose to translate."""
    wanted = set(request.session.get(SESSION_KEY, []))
    for review in reviews:
        review.translation = cached_translation(review.comment) if review.pk in wanted and review.comment else None
    return reviews
