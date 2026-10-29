from django.db import models
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from courses.models import Course


class ReviewSummary(models.Model):
    """An AI summary of one course's reviews for one month or year.
    Saved so we only ask Groq again when new reviews come in."""

    PERIOD_MONTHLY = 'monthly'
    PERIOD_YEARLY = 'yearly'
    PERIOD_CHOICES = [(PERIOD_MONTHLY, 'This month'), (PERIOD_YEARLY, 'This year')]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='summaries')
    period_type = models.TextField(choices=PERIOD_CHOICES)
    period_start = models.DateField()
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)
    praises = models.TextField(blank=True, null=True)
    complaints = models.TextField(blank=True, null=True)
    changes = models.TextField(blank=True, null=True)
    # When the summary was (re)written. Reviews newer than this make it out of date.
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = 'review_summaries'
        unique_together = ('course', 'period_type', 'period_start')


class Conversation(models.Model):
    """One chat with the AI assistant, listed in the chat sidebar so the user can reopen it."""

    TITLE_LENGTH = 60  # the first question, cut short, names the chat

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_conversations')
    title = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    # Moves to now on every new question, so the newest chats come first
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = 'ai_conversations'
        ordering = ['-updated_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('ai_assistant:conversation', args=[self.pk])


class ChatMessage(models.Model):
    """One question and the AI's answer inside a conversation."""

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    question = models.TextField()
    answer = models.TextField()
    # The cited courses as [{"id", "name", "college"}], saved so old answers keep their links
    sources = models.JSONField(default=list)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = 'ai_messages'
        ordering = ['created_at']
