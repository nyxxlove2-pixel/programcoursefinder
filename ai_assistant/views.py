from django.contrib import messages
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from accounts.models import User
from accounts.utils import role_required
from core.utils import redirect_back
from courses.models import Course
from courses.utils import user_location, with_ratings
from organizations.models import Organization
from organizations.utils import get_own_organization
from reviews.models import Review

from .assistant import answer_question
from .forms import QuestionForm
from .groq import AIUnavailable
from .models import ReviewSummary
from .summaries import summary_status, write_summary
from .translation import remember_translated, translate
from .utils import BUSY_MESSAGE, limit_message, take_ai_request

CHAT_SESSION_KEY = 'assistant_chat'
MAX_CHAT_TURNS = 6  # older questions drop off so the session stays small
EXAMPLE_QUESTIONS = [
    'Which IT course near me has good reviews?',
    'What can I study for under ₱40,000 a year?',
    'What do students say about Nursing courses?',
]


# ---------- Assistant (User accounts) ----------

@role_required(User.ROLE_USER)
def assistant(request):
    form = QuestionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        ask_and_save(request, form.cleaned_data['question'])
        return redirect('ai_assistant:assistant')
    return render(request, 'ai_assistant/assistant.html', {
        'form': form,
        'chat': request.session.get(CHAT_SESSION_KEY, []),
        'has_location': user_location(request) is not None,
        'example_questions': EXAMPLE_QUESTIONS,
    })


def ask_and_save(request, question):
    """Ask the AI and add the question and answer to this visitor's chat."""
    if not take_ai_request(request.app_user):
        messages.error(request, limit_message())
        return
    try:
        answer, sources = answer_question(question, request.app_user, user_location(request))
    except AIUnavailable:
        messages.error(request, BUSY_MESSAGE)
        return
    turn = {
        'question': question,
        'answer': answer,
        'sources': [{'id': c.pk, 'name': c.name, 'college': c.organization.name} for c in sources],
    }
    chat = request.session.get(CHAT_SESSION_KEY, []) + [turn]
    request.session[CHAT_SESSION_KEY] = chat[-MAX_CHAT_TURNS:]


@role_required(User.ROLE_USER)
@require_POST
def clear_chat(request):
    request.session.pop(CHAT_SESSION_KEY, None)
    return redirect('ai_assistant:assistant')


# ---------- Translation (any logged-in account) ----------

@role_required()
@require_POST
def translate_review(request, pk):
    # Public reviews, plus reviews on the college's own courses
    visible = Q(course__organization__status=Organization.STATUS_APPROVED) | Q(course__organization__owner=request.app_user)
    review = get_object_or_404(Review.objects.filter(visible), pk=pk)
    if not review.comment:
        return redirect_back(request, review.get_absolute_url())
    if not take_ai_request(request.app_user):
        messages.error(request, limit_message())
        return redirect_back(request, review.get_absolute_url())
    try:
        translate(review.comment)
        remember_translated(request, review.pk)
    except AIUnavailable:
        messages.error(request, BUSY_MESSAGE)
    return redirect_back(request, review.get_absolute_url())


# ---------- Review summaries (Organization accounts) ----------

@role_required(User.ROLE_ORGANIZATION)
def summaries(request):
    organization = get_own_organization(request.app_user)
    if organization is None:
        return redirect('organizations:edit')
    courses = list(with_ratings(organization.courses.all()))
    for course in courses:
        course.periods = [summary_status(course, period) for period, _ in ReviewSummary.PERIOD_CHOICES]
    return render(request, 'ai_assistant/summaries.html', {'courses': courses})


@role_required(User.ROLE_ORGANIZATION)
@require_POST
def generate_summary(request, course_pk, period_type):
    # Colleges can only summarize their own courses
    course = get_object_or_404(Course, pk=course_pk, organization__owner=request.app_user)
    if period_type not in dict(ReviewSummary.PERIOD_CHOICES):
        raise Http404
    status = summary_status(course, period_type)
    if not status['enough']:
        messages.info(request, 'Not enough reviews yet for a summary.')
    elif not status['stale']:
        messages.info(request, 'This summary is already up to date.')
    elif not take_ai_request(request.app_user):
        messages.error(request, limit_message())
    else:
        write_summary_or_warn(request, course, period_type)
    return redirect(reverse('ai_assistant:summaries') + f'#course-{course.pk}')


def write_summary_or_warn(request, course, period_type):
    try:
        write_summary(course, period_type)
        messages.success(request, f'Summary for {course.name} is ready.')
    except AIUnavailable:
        messages.error(request, BUSY_MESSAGE)
