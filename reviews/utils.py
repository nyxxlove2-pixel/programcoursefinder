from datetime import timedelta

from django.db.models import Avg, Count, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone

from courses.utils import public_courses
from notifications.utils import notify
from organizations.models import Organization

from .models import Review, ReviewReaction


def with_reaction_counts(reviews):
    """Add review.likes and review.dislikes."""
    return reviews.annotate(
        likes=Count('reactions', filter=Q(reactions__reaction=ReviewReaction.LIKE)),
        dislikes=Count('reactions', filter=Q(reactions__reaction=ReviewReaction.DISLIKE)),
    )


def reviews_for_page(reviews, viewer=None):
    """Reviews ready to show: author, replies, like/dislike counts,
    review.my_reaction (what the viewer picked, or None), and
    review.can_react (only User accounts, and never on their own review). Returns a list."""
    reviews = reviews.select_related('user', 'course__organization').prefetch_related('replies')
    reviews = list(with_reaction_counts(reviews))
    my_reactions = {}
    if viewer:
        my_reactions = dict(
            ReviewReaction.objects.filter(user=viewer, review__in=reviews).values_list('review_id', 'reaction')
        )
    viewer_is_user = viewer is not None and not viewer.is_organization
    for review in reviews:
        review.my_reaction = my_reactions.get(review.id)
        review.can_react = viewer_is_user and review.user_id != viewer.id
    return reviews


def toggle_reaction(review, user, reaction):
    """Like or dislike a review. Picking the same reaction again removes it."""
    existing = ReviewReaction.objects.filter(review=review, user=user).first()
    if existing and existing.reaction == reaction:
        existing.delete()
    else:
        ReviewReaction.objects.update_or_create(review=review, user=user, defaults={'reaction': reaction})


def add_reaction_counts(courses):
    """Set course.likes and course.dislikes (over all its reviews). Returns a list."""
    courses = list(courses)
    rows = (
        ReviewReaction.objects.filter(review__course__in=courses)
        .values('review__course_id', 'reaction')
        .annotate(total=Count('reaction'))
    )
    totals = {(row['review__course_id'], row['reaction']): row['total'] for row in rows}
    for course in courses:
        course.likes = totals.get((course.id, ReviewReaction.LIKE), 0)
        course.dislikes = totals.get((course.id, ReviewReaction.DISLIKE), 0)
    return courses


def organization_review_stats(organization):
    """Numbers for the organization dashboard, over all of its courses."""
    reviews = Review.objects.filter(course__organization=organization)
    reactions = ReviewReaction.objects.filter(review__in=reviews)
    stats = reviews.aggregate(average_rating=Avg('rating'), review_count=Count('id'))
    stats['needs_reply'] = reviews.filter(replies__isnull=True).count()
    stats['likes'] = reactions.filter(reaction=ReviewReaction.LIKE).count()
    stats['dislikes'] = reactions.filter(reaction=ReviewReaction.DISLIKE).count()
    return stats


def last_months(count):
    """The first day of each of the last `count` months, oldest first."""
    month = timezone.localdate().replace(day=1)
    months = []
    for _ in range(count):
        months.append(month)
        month = (month - timedelta(days=1)).replace(day=1)
    return months[::-1]


def monthly_trend(reviews, months=12):
    """One row per month: review count, average rating, and bar height (percent of the busiest month)."""
    month_starts = last_months(months)
    rows = list(
        reviews.filter(created_at__date__gte=month_starts[0])
        .annotate(month=TruncMonth('created_at')).values('month').order_by()
        .annotate(count=Count('id'), average=Avg('rating'))
    )
    by_month = {row['month'].date(): row for row in rows}
    busiest = max([row['count'] for row in rows], default=0) or 1
    trend = []
    for month in month_starts:
        row = by_month.get(month, {'count': 0, 'average': None})
        trend.append({'month': month, 'count': row['count'], 'average': row['average'],
                      'percent': row['count'] * 100 // busiest})
    return trend


def rating_distribution(reviews):
    """How many reviews gave 5, 4, 3, 2, and 1 stars, with the percent of all reviews."""
    counts = dict(reviews.values_list('rating').order_by().annotate(total=Count('id')))
    total = sum(counts.values()) or 1
    return [
        {'stars': stars, 'count': counts.get(stars, 0), 'percent': counts.get(stars, 0) * 100 // total}
        for stars in range(5, 0, -1)
    ]


def notify_review_saved(review, is_new):
    """Tell the college about a new or changed review, and its new average rating."""
    course = review.course
    average = course.reviews.aggregate(average=Avg('rating'))['average']
    action = 'posted' if is_new else 'updated'
    notify(
        course.organization.owner,
        f'{review.user.full_name} {action} a {review.rating}-star review on {course.name}. '
        f'Average rating is now {average:.1f}.',
        review.get_absolute_url(),
    )


def notify_reply(review):
    """Tell the reviewer that the college answered them."""
    notify(
        review.user,
        f'{review.course.organization.name} replied to your review of {review.course.name}.',
        review.get_absolute_url(),
    )


def report_target(target_type, target_id):
    """The public review, course, or college being reported, or None if it is not found."""
    targets = {
        'review': Review.objects.filter(course__organization__status=Organization.STATUS_APPROVED),
        'course': public_courses(),
        'organization': Organization.objects.filter(status=Organization.STATUS_APPROVED),
    }
    if target_type not in targets:
        return None
    return targets[target_type].filter(pk=target_id).first()
