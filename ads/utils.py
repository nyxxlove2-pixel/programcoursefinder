from organizations.models import Organization

from .models import Ad


def random_live_ad():
    """One approved ad from a verified college, picked at random so every college gets turns."""
    return Ad.objects.filter(
        status=Ad.STATUS_APPROVED, organization__status=Organization.STATUS_APPROVED
    ).select_related('organization', 'course').order_by('?').first()
