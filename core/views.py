from django.shortcuts import render

from accounts.utils import get_current_user, redirect_home
from courses.utils import add_distances, get_compare_ids, public_courses


def home(request):
    # Logged-in accounts skip the landing page and go straight to their own area
    user = get_current_user(request)
    if user:
        return redirect_home(user)

    # Landing page with a few verified courses to show off.
    # Visitors are not logged in, so there is no location to measure distance from.
    featured_courses = add_distances(public_courses()[:3], None)
    return render(request, 'core/home.html', {
        'featured_courses': featured_courses,
        'compare_ids': get_compare_ids(request),
    })
