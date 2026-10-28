from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.defaultfilters import pluralize
from django.views.decorators.http import require_POST

from accounts.models import User
from ads.utils import random_live_ad
from accounts.utils import get_current_user, role_required
from ai_assistant.translation import attach_translations
from core.utils import redirect_back
from organizations.utils import get_own_organization
from reviews.forms import ReviewForm
from reviews.utils import reviews_for_page

from .csv_upload import read_course_rows, save_courses, template_csv
from .forms import CourseForm, CourseUploadForm, SearchForm
from .utils import (
    add_distances, get_compare_ids, public_courses, search_courses, toggle_compare, user_location,
)


# ---------- Public pages ----------

def search(request):
    form = SearchForm(request.GET or None)
    filters = form.cleaned_data if form.is_valid() else {}
    location = user_location(request)
    # The form's field names match search_courses' arguments, so pass them straight in
    courses = search_courses(user_location=location, **filters)
    return render(request, 'courses/search.html', {
        'form': form,
        'courses': courses,
        'has_location': location is not None,
        'compare_ids': get_compare_ids(request),
        'ad': random_live_ad(),
    })


def detail(request, pk):
    course = get_object_or_404(public_courses(), pk=pk)
    course = add_distances([course], user_location(request))[0]
    user = get_current_user(request)
    reviews = attach_translations(reviews_for_page(course.reviews.all(), user), request)
    return render(request, 'courses/detail.html', {
        'course': course,
        'compare_ids': get_compare_ids(request),
        'reviews': reviews,
        'review_form': review_form_for(course, user),
    })


def review_form_for(course, user):
    """The review form for a User account, filled in if they already reviewed this course.
    Visitors and organizations get None, because they cannot review."""
    if user is None or user.is_organization:
        return None
    own_review = course.reviews.filter(user=user).first()
    return ReviewForm(instance=own_review)


@require_POST
def compare_toggle(request, pk):
    course = get_object_or_404(public_courses(), pk=pk)
    messages.info(request, toggle_compare(request, course.pk))
    return redirect_back(request, 'courses:compare')


def compare(request):
    courses = public_courses().filter(pk__in=get_compare_ids(request))
    courses = add_distances(courses, user_location(request))
    return render(request, 'courses/compare.html', {'courses': courses})


# ---------- Organization pages ----------

@role_required(User.ROLE_ORGANIZATION)
def course_form(request, pk=None):
    """Add a new course (no pk) or edit an existing one (with pk)."""
    organization = get_own_organization(request.app_user)
    if organization is None:
        return redirect('organizations:edit')

    course = get_object_or_404(organization.courses, pk=pk) if pk else None
    form = CourseForm(request.POST or None, instance=course)
    if request.method == 'POST' and form.is_valid():
        course = form.save(commit=False)
        course.organization = organization
        course.save()
        messages.success(request, 'Course saved.')
        return redirect('organizations:dashboard')
    return render(request, 'courses/course_form.html', {'form': form, 'course': course})


UPLOAD_STEPS = [
    'Download the template and fill in one course per row.',
    'Write tuition as plain numbers, like 40000. Leave term tuition empty if there is none.',
    'Save as "CSV UTF-8" and upload. If any row has a problem, nothing is added.',
]


@role_required(User.ROLE_ORGANIZATION)
def bulk_upload(request):
    """Add many courses from one CSV file. Nothing is saved unless every row is valid."""
    organization = get_own_organization(request.app_user)
    if organization is None:
        return redirect('organizations:edit')

    form = CourseUploadForm(request.POST or None, request.FILES or None)
    errors = []
    if request.method == 'POST' and form.is_valid():
        course_forms, errors = read_course_rows(form.cleaned_data['file'])
        if not errors:
            save_courses(course_forms, organization)
            messages.success(request, f'{len(course_forms)} course{pluralize(len(course_forms))} added.')
            return redirect('organizations:dashboard')
    return render(request, 'courses/bulk_upload.html', {'form': form, 'errors': errors, 'steps': UPLOAD_STEPS})


@role_required(User.ROLE_ORGANIZATION)
def csv_template(request):
    response = HttpResponse(template_csv(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="courses_template.csv"'
    return response


@role_required(User.ROLE_ORGANIZATION)
@require_POST
def delete(request, pk):
    organization = get_own_organization(request.app_user)
    course = get_object_or_404(organization.courses, pk=pk)
    course.delete()
    messages.success(request, 'Course deleted.')
    return redirect('organizations:dashboard')
