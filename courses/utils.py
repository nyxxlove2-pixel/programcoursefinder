from math import asin, cos, radians, sin, sqrt

from django.db.models import Avg, Count, Q

from accounts.utils import get_current_user
from organizations.models import Organization

from .models import Course

COMPARE_SESSION_KEY = 'compare_ids'
MAX_COMPARE = 3

# "Sort by" options on the search page. "Recommended" (the empty value)
# shows the nearest courses first when we know where the user lives.
SORT_CHOICES = [
    ('', 'Recommended'),
    ('tuition_low', 'Lowest tuition'),
    ('tuition_high', 'Highest tuition'),
    ('name', 'Name (A to Z)'),
]
SORT_ORDERS = {
    'tuition_low': 'yearly_tuition',
    'tuition_high': '-yearly_tuition',
    'name': 'name',
}


def user_location(request):
    """The logged-in user's shared (lat, lng), or None."""
    user = get_current_user(request)
    if user is None or user.is_organization or not hasattr(user, 'profile'):
        return None
    return user.profile.location()


def distance_km(point_a, point_b):
    """Straight-line distance in km between two (lat, lng) points (haversine formula)."""
    lat1, lng1, lat2, lng2 = map(radians, map(float, (*point_a, *point_b)))
    a = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lng2 - lng1) / 2) ** 2
    return round(2 * 6371 * asin(sqrt(a)), 1)


def add_distances(courses, user_location):
    """Set course.distance on each course (None if unknown). Returns a list."""
    courses = list(courses)
    for course in courses:
        org = course.organization
        if user_location and org.latitude and org.longitude:
            course.distance = distance_km(user_location, (org.latitude, org.longitude))
        else:
            course.distance = None
    return courses


def with_ratings(courses):
    """Add course.average_rating (None if no reviews) and course.review_count."""
    return courses.annotate(average_rating=Avg('reviews__rating'), review_count=Count('reviews'))


def public_courses():
    """Courses from verified colleges only, with their ratings. Everything public starts here."""
    courses = Course.objects.filter(
        organization__status=Organization.STATUS_APPROVED
    ).select_related('organization')
    return with_ratings(courses)


def search_courses(query='', college=None, min_tuition=None, max_tuition=None,
                   max_distance=None, sort='', user_location=None):
    """Filter public courses, then sort them the way the user picked."""
    courses = public_courses()
    if query:
        # Match the course name OR the college name
        courses = courses.filter(Q(name__icontains=query) | Q(organization__name__icontains=query))
    if college:
        courses = courses.filter(organization=college)
    if min_tuition is not None:
        courses = courses.filter(yearly_tuition__gte=min_tuition)
    if max_tuition is not None:
        courses = courses.filter(yearly_tuition__lte=max_tuition)
    if sort in SORT_ORDERS:
        courses = courses.order_by(SORT_ORDERS[sort])

    # Distance is worked out in Python, so these steps run on the list
    courses = add_distances(courses, user_location)
    if max_distance is not None:
        courses = [course for course in courses if course.distance is not None and course.distance <= max_distance]
    if user_location and not sort:
        # "Recommended" means nearest first; unknown distances go to the end
        courses.sort(key=lambda c: (c.distance is None, c.distance or 0))
    return courses


def get_compare_ids(request):
    return request.session.get(COMPARE_SESSION_KEY, [])


def toggle_compare(request, course_id):
    """Add the course to the compare list, or remove it if already there.
    Returns a message for the user."""
    ids = get_compare_ids(request)
    if course_id in ids:
        ids.remove(course_id)
        message = 'Removed from compare.'
    elif len(ids) >= MAX_COMPARE:
        return f'You can compare up to {MAX_COMPARE} courses. Remove one first.'
    else:
        ids.append(course_id)
        message = 'Added to compare.'
    request.session[COMPARE_SESSION_KEY] = ids
    return message
