from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import User
from accounts.utils import role_required
from ai_assistant.translation import attach_translations
from core.utils import redirect_back
from courses.utils import public_courses
from organizations.models import Organization
from organizations.utils import get_own_organization

from .forms import ReplyForm, ReportForm, ReviewForm
from .models import Review, ReviewReaction
from .utils import notify_reply, notify_review_saved, report_target, reviews_for_page, toggle_reaction


# ---------- User actions ----------

@role_required(User.ROLE_USER)
@require_POST
def save_review(request, course_pk):
    """Post a review, or update it if this user already reviewed the course."""
    course = get_object_or_404(public_courses(), pk=course_pk)
    own_review = course.reviews.filter(user=request.app_user).first()
    form = ReviewForm(request.POST, instance=own_review)
    if not form.is_valid():
        messages.error(request, 'Please pick a star rating.')
        return redirect(course)

    review = form.save(commit=False)
    review.course = course
    review.user = request.app_user
    review.save()
    notify_review_saved(review, is_new=own_review is None)
    messages.success(request, 'Thanks! Your review is posted.')
    return redirect(review)


@role_required(User.ROLE_USER)
@require_POST
def react(request, pk):
    review = get_object_or_404(Review, pk=pk, course__organization__status=Organization.STATUS_APPROVED)
    reaction = request.POST.get('reaction')
    if review.user_id == request.app_user.id:
        messages.info(request, 'You cannot like or dislike your own review.')
    elif reaction in (ReviewReaction.LIKE, ReviewReaction.DISLIKE):
        toggle_reaction(review, request.app_user, reaction)
    return redirect(review)


@role_required()
def report(request, target_type, target_id):
    """Any logged-in account can report a review, course, or college.
    The developer checks open reports in Django admin."""
    target = report_target(target_type, target_id)
    if target is None:
        raise Http404
    form = ReportForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        new_report = form.save(commit=False)
        new_report.reporter = request.app_user
        new_report.target_type = target_type
        new_report.target_id = target.pk
        new_report.save()
        messages.success(request, 'Thanks. Your report was sent and will be checked.')
        return redirect(target)
    return render(request, 'reviews/report.html', {'form': form, 'target': target})


# ---------- Organization pages ----------

@role_required(User.ROLE_ORGANIZATION)
def organization_reviews(request):
    """Every review on this college's courses. ?show=needs_reply lists unanswered ones only."""
    organization = get_own_organization(request.app_user)
    if organization is None:
        return redirect('organizations:edit')

    reviews = Review.objects.filter(course__organization=organization)
    needs_reply_only = request.GET.get('show') == 'needs_reply'
    if needs_reply_only:
        reviews = reviews.filter(replies__isnull=True)
    return render(request, 'reviews/organization_reviews.html', {
        'reviews': attach_translations(reviews_for_page(reviews, request.app_user), request),
        'reply_form': ReplyForm(auto_id=False),
        'needs_reply_only': needs_reply_only,
    })


@role_required(User.ROLE_ORGANIZATION)
@require_POST
def reply(request, pk):
    # Colleges can only answer reviews on their own courses
    organization = get_own_organization(request.app_user)
    review = get_object_or_404(Review, pk=pk, course__organization=organization)
    form = ReplyForm(request.POST)
    if form.is_valid():
        new_reply = form.save(commit=False)
        new_reply.review = review
        new_reply.user = request.app_user
        new_reply.save()
        notify_reply(review)
        messages.success(request, 'Reply posted.')
    return redirect_back(request, 'reviews:organization_reviews')
