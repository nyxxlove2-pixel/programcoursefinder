import re

from django.db import models

from courses.models import Course
from organizations.models import Organization

# The 11-character video id inside youtu.be/ID, youtube.com/watch?v=ID, /shorts/ID, or /embed/ID
YOUTUBE_ID = re.compile(r'(?:youtu\.be/|youtube\.com/(?:watch\?v=|shorts/|embed/))([\w-]{11})')


def youtube_id(url):
    """The video id from a YouTube link, or None if it is not one."""
    match = YOUTUBE_ID.search(url or '')
    return match.group(1) if match else None


class Ad(models.Model):
    TYPE_BANNER = 'banner'
    TYPE_VIDEO = 'video'
    TYPE_CHOICES = [(TYPE_BANNER, 'Banner image'), (TYPE_VIDEO, 'YouTube video')]
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='ads')
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, blank=True, null=True, related_name='ads')
    title = models.TextField()
    ad_type = models.TextField(choices=TYPE_CHOICES, default=TYPE_BANNER)
    media_url = models.URLField()
    status = models.TextField(choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'ads'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def target_url(self):
        """Where the ad leads: the chosen course, or else the college page."""
        return (self.course or self.organization).get_absolute_url()

    def embed_url(self):
        # youtube-nocookie does not track viewers until they press play
        return f'https://www.youtube-nocookie.com/embed/{youtube_id(self.media_url)}'
