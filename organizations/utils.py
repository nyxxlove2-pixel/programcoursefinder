from django.urls import reverse
from django.utils import timezone

from notifications.utils import notify

from .models import Organization, VerificationDocument


def get_own_organization(user):
    """Return the organization owned by this account, or None."""
    return Organization.objects.filter(owner=user).first()


def document_rows(organization):
    """One row per required document, showing whether it is uploaded yet."""
    uploaded = {doc.doc_type: doc for doc in organization.documents.all()}
    return [
        {'label': label, 'document': uploaded.get(doc_type)}
        for doc_type, label in VerificationDocument.DOC_TYPE_CHOICES
    ]


def notify_status(organization):
    """Tell the college owner their verification status changed."""
    message = f'Verification status: {organization.get_status_display()}.'
    if organization.status_reason:
        message += f' {organization.status_reason}'
    notify(organization.owner, message, reverse('organizations:dashboard'))


def change_status(organization, status, reason=''):
    """Approve, ask for changes, or reject a college, then notify it.
    Used by the super admin dashboard and by Django admin."""
    organization.status = status
    organization.status_reason = reason or None
    organization.verified_at = timezone.now() if status == Organization.STATUS_APPROVED else None
    organization.save()
    notify_status(organization)
