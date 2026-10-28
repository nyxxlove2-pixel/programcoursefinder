from django.db import models
from django.urls import reverse

from accounts.models import User


class Organization(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_NEEDS_CHANGES = 'needs_changes'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_NEEDS_CHANGES, 'Needs changes'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='organization')
    name = models.TextField()
    description = models.TextField(blank=True, null=True)
    phone = models.TextField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    facebook_url = models.URLField(blank=True, null=True)
    instagram_url = models.URLField(blank=True, null=True)
    tiktok_url = models.URLField(blank=True, null=True)
    youtube_url = models.URLField(blank=True, null=True)
    status = models.TextField(choices=STATUS_CHOICES, default=STATUS_PENDING)
    status_reason = models.TextField(blank=True, null=True)
    verified_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'organizations'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('organizations:detail', args=[self.pk])

    def map_url(self):
        """Google Maps link to the campus pin, or '' if there is no pin."""
        if self.latitude is None or self.longitude is None:
            return ''
        return f'https://www.google.com/maps?q={self.latitude},{self.longitude}'

    @property
    def is_verified(self):
        return self.status == self.STATUS_APPROVED


class VerificationDocument(models.Model):
    DOC_TYPE_CHOICES = [
        ('government_recognition', 'Government recognition / permit (CHED or TESDA)'),
        ('sec_registration', 'Business / SEC registration'),
        ('authorization_letter', 'Authorization letter'),
        ('valid_id', 'Valid ID of representative'),
        ('proof_of_official_channels', 'Proof of official channels'),
    ]

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name='documents'
    )
    doc_type = models.TextField(choices=DOC_TYPE_CHOICES)
    # Saved in the file_url column as a file path
    file = models.FileField(upload_to='verification/', db_column='file_url')
    uploaded_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'verification_documents'
        unique_together = ('organization', 'doc_type')

    def __str__(self):
        return f'{self.organization} - {self.get_doc_type_display()}'
