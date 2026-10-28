from django.db import models
from django.urls import reverse

from organizations.models import Organization


class Course(models.Model):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name='courses'
    )
    name = models.TextField()
    description = models.TextField(blank=True, null=True)
    yearly_tuition = models.DecimalField(max_digits=12, decimal_places=2)
    term_tuition = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'courses'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.organization})'

    def get_absolute_url(self):
        return reverse('courses:detail', args=[self.pk])


class CourseMedia(models.Model):
    MEDIA_TYPE_CHOICES = [('image', 'Image'), ('video', 'Video')]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='media')
    media_type = models.TextField(choices=MEDIA_TYPE_CHOICES)
    url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'course_media'
