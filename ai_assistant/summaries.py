import json
from datetime import date, timedelta

from django.db.models import Avg
from django.utils import timezone

from .groq import AIUnavailable, ask_groq
from .models import ReviewSummary

MIN_REVIEWS = 3  # fewer than this and we show "not enough reviews yet" instead of a summary

SYSTEM_PROMPT = """You summarize student reviews of one college course for the college.
Use ONLY the reviews given. Always write in English, even when a review is in another language.
Reply with a JSON object with exactly these keys:
"praises": the main things students like (up to 3 short points, one per line),
"complaints": the main problems (up to 3 short points, one per line, or "None mentioned"),
"changes": how this period differs from the previous summary, in 1 or 2 sentences
(if there is no previous summary, say it is the first summary)."""


def period_start(period_type, today=None):
    """First day of the current month or year."""
    today = today or timezone.localdate()
    if period_type == ReviewSummary.PERIOD_MONTHLY:
        return today.replace(day=1)
    return date(today.year, 1, 1)


def previous_period_start(period_type, start):
    if period_type == ReviewSummary.PERIOD_MONTHLY:
        return (start - timedelta(days=1)).replace(day=1)
    return date(start.year - 1, 1, 1)


def period_reviews(course, period_type):
    return course.reviews.filter(created_at__date__gte=period_start(period_type))


def summary_status(course, period_type):
    """What the summaries page shows for one course and period:
    {'summary': saved summary or None, 'review_count': n, 'enough': bool, 'stale': bool}"""
    reviews = period_reviews(course, period_type)
    summary = ReviewSummary.objects.filter(
        course=course, period_type=period_type, period_start=period_start(period_type)
    ).first()
    stale = summary is None or reviews.filter(created_at__gt=summary.created_at).exists()
    review_count = reviews.count()
    return {
        'period_type': period_type,
        'label': dict(ReviewSummary.PERIOD_CHOICES)[period_type],
        'summary': summary,
        'review_count': review_count,
        'enough': review_count >= MIN_REVIEWS,
        'min_reviews': MIN_REVIEWS,
        'stale': stale,
    }


def build_prompt(course, reviews, previous):
    lines = [f'Course: {course.name}', 'Reviews this period:']
    lines += [f'- {review.rating} stars: {review.comment or "(no comment)"}' for review in reviews]
    if previous:
        lines.append(f'Previous summary: praises: {previous.praises}; complaints: {previous.complaints}')
    else:
        lines.append('Previous summary: none')
    return '\n'.join(lines)


def as_text(value):
    """The AI sometimes sends a list of points instead of text; store one point per line."""
    if isinstance(value, list):
        return '\n'.join(str(point) for point in value)
    return str(value or '')


def write_summary(course, period_type):
    """Ask the AI for a fresh summary and save it. The average rating is worked
    out by us, not the AI, so the number is always exact."""
    start = period_start(period_type)
    reviews = list(period_reviews(course, period_type)[:60])
    previous = ReviewSummary.objects.filter(
        course=course, period_type=period_type, period_start=previous_period_start(period_type, start)
    ).first()
    try:
        result = json.loads(ask_groq(SYSTEM_PROMPT, build_prompt(course, reviews, previous), json_mode=True))
    except json.JSONDecodeError as error:
        raise AIUnavailable('The AI reply was not valid JSON') from error

    ReviewSummary.objects.update_or_create(
        course=course, period_type=period_type, period_start=start,
        defaults={
            'average_rating': period_reviews(course, period_type).aggregate(average=Avg('rating'))['average'],
            'praises': as_text(result.get('praises')),
            'complaints': as_text(result.get('complaints')),
            'changes': as_text(result.get('changes')),
            'created_at': timezone.now(),
        },
    )
