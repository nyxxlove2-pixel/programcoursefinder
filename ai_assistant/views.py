from django.contrib import messages
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
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
from .models import ChatMessage, Conversation, ReviewSummary
from .summaries import summary_status, write_summary
from .translation import remember_translated, translate
from .utils import BUSY_MESSAGE, limit_message, take_ai_request

EXAMPLE_QUESTIONS = [
    'Which IT course near me has good reviews?',
    'What can I study for under ₱40,000 a year?',
    'What do students say about Nursing courses?',
]


# ---------- Assistant (User accounts) ----------

@role_required(User.ROLE_USER)
def assistant(request, pk=None):
    """The chat page. Without a pk it starts a new chat; with one it opens a saved chat."""
    conversation = None
    if pk is not None:
        conversation = get_object_or_404(Conversation, pk=pk, user=request.app_user)
    form = QuestionForm(request.POST or None)
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'fetch':
        return answer_for_chat(request, form, conversation)
    if request.method == 'POST' and form.is_valid():
        message, error = ask_and_save(request, form.cleaned_data['question'], conversation)
        if error:
            messages.error(request, error)
            return redirect(request.path)
        return redirect(message.conversation)
    full_name = request.app_user.full_name or ''
    return render(request, 'ai_assistant/assistant.html', {
        'form': form,
        'conversation': conversation,
        'chat': conversation.messages.all() if conversation else [],
        'conversations': request.app_user.ai_conversations.all(),
        'first_name': full_name.split()[0] if full_name.strip() else '',
        'has_location': user_location(request) is not None,
        'example_questions': EXAMPLE_QUESTIONS,
    })


def answer_for_chat(request, form, conversation):
    """Reply to the chat page's fetch() with the new answer and its sidebar link as HTML,
    so the page can animate the answer in and keep the history list up to date."""
    if not form.is_valid():
        return JsonResponse({'error': 'Please type a question (up to 500 characters).'}, status=400)
    message, error = ask_and_save(request, form.cleaned_data['question'], conversation)
    if error:
        return JsonResponse({'error': error}, status=503)
    return JsonResponse({
        'html': render_to_string('ai_assistant/chat_answer.html', {'turn': message}, request=request),
        'history_html': render_to_string('ai_assistant/chat_history_link.html', {
            'item': message.conversation, 'conversation': message.conversation,
        }, request=request),
        'conversation_id': message.conversation.pk,
        'conversation_url': message.conversation.get_absolute_url(),
    })


def ask_and_save(request, question, conversation):
    """Ask the AI and save the question and answer, starting a new conversation if needed.
    Returns (saved message, None), or (None, error message for the user)."""
    if not take_ai_request(request.app_user):
        return None, limit_message()
    try:
        answer, sources = answer_question(question, request.app_user, user_location(request))
    except AIUnavailable:
        return None, BUSY_MESSAGE
    if conversation is None:
        conversation = Conversation.objects.create(user=request.app_user, title=question[:Conversation.TITLE_LENGTH])
    else:
        conversation.updated_at = timezone.now()
        conversation.save(update_fields=['updated_at'])
    message = ChatMessage.objects.create(
        conversation=conversation,
        question=question,
        answer=answer,
        sources=[{'id': c.pk, 'name': c.name, 'college': c.organization.name} for c in sources],
    )
    return message, None


@role_required(User.ROLE_USER)
@require_POST
def delete_conversation(request, pk):
    conversation = get_object_or_404(Conversation, pk=pk, user=request.app_user)
    conversation.delete()
    messages.success(request, 'Chat deleted.')
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
