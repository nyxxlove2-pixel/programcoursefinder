from django.db import models
from django.utils import timezone

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
