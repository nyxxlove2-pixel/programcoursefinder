from django.db import models

from accounts.models import User
from courses.models import Course


class Review(models.Model):
    RATING_CHOICES = [(1, '1 star'), (2, '2 stars'), (3, '3 stars'), (4, '4 stars'), (5, '5 stars')]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.SmallIntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'reviews'
        unique_together = ('course', 'user')  # one review per user per course
        ordering = ['-created_at']

    def __str__(self):
        return f'Review of {self.course.name} by {self.user.full_name}'

    def get_absolute_url(self):
        # Jump straight to this review on the course page
        return f'{self.course.get_absolute_url()}#review-{self.pk}'


class ReviewReply(models.Model):
    # Only the organization that owns the course replies. It cannot delete reviews.
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='replies')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='review_replies')
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'review_replies'
        ordering = ['created_at']


class ReviewReaction(models.Model):
    LIKE = 'like'
    DISLIKE = 'dislike'
    REACTION_CHOICES = [(LIKE, 'Like'), (DISLIKE, 'Dislike')]

    # The table's primary key is (review_id, user_id): one reaction per user per review
    pk = models.CompositePrimaryKey('review_id', 'user_id')
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='review_reactions')
    reaction = models.TextField(choices=REACTION_CHOICES)

    class Meta:
        managed = False
        db_table = 'review_reactions'


class Report(models.Model):
    STATUS_OPEN = 'open'
    STATUS_RESOLVED = 'resolved'
    STATUS_CHOICES = [(STATUS_OPEN, 'Open'), (STATUS_RESOLVED, 'Resolved')]
    TARGET_CHOICES = [
        ('review', 'Review'),
        ('course', 'Course'),
        ('organization', 'Organization'),
    ]

    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    target_type = models.TextField(choices=TARGET_CHOICES)
    target_id = models.BigIntegerField()
    reason = models.TextField()
    status = models.TextField(choices=STATUS_CHOICES, default=STATUS_OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'reports'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_target_type_display()} #{self.target_id}'
