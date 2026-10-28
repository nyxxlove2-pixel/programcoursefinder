from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from organizations.models import Organization, VerificationDocument
from organizations.utils import change_status, document_rows

from .forms import DecisionForm

# Only the developer's Django superuser account (the one used for /admin/) gets in.
# Everyone else is sent to the Django admin login page.
superuser_required = user_passes_test(lambda user: user.is_active and user.is_superuser, login_url='admin:login')


@superuser_required
def dashboard(request):
    """Every college grouped by status, pending first. ?status=... picks the group, ?q= searches by name."""
    status = request.GET.get('status', Organization.STATUS_PENDING)
    if status not in dict(Organization.STATUS_CHOICES):
        status = Organization.STATUS_PENDING
    query = request.GET.get('q', '').strip()

    organizations = Organization.objects.filter(status=status).select_related('owner').annotate(
        document_count=Count('documents', distinct=True),
        course_count=Count('courses', distinct=True),
    ).order_by('created_at')  # oldest waiting first
    if query:
        organizations = organizations.filter(Q(name__icontains=query) | Q(owner__email__icontains=query))

    counts = dict(Organization.objects.values_list('status').annotate(total=Count('id')).order_by())
    status_cards = [
        {'value': value, 'label': label, 'count': counts.get(value, 0), 'active': value == status}
        for value, label in Organization.STATUS_CHOICES
    ]
    return render(request, 'superadmin/dashboard.html', {
        'organizations': organizations,
        'status_cards': status_cards,
        'status': status,
        'status_label': dict(Organization.STATUS_CHOICES)[status],
        'query': query,
        'documents_needed': len(VerificationDocument.DOC_TYPE_CHOICES),
    })


@superuser_required
def review(request, pk):
    """One college's details and documents, with the approve / needs changes / reject form."""
    organization = get_object_or_404(Organization.objects.select_related('owner'), pk=pk)
    form = DecisionForm(request.POST or None, initial={'reason': organization.status_reason})
    if request.method == 'POST' and form.is_valid():
        change_status(organization, form.cleaned_data['decision'], form.cleaned_data['reason'])
        messages.success(request, f'{organization.name} is now "{organization.get_status_display()}". The college was notified.')
        return redirect('superadmin:dashboard')

    rows = document_rows(organization)
    return render(request, 'superadmin/review.html', {
        'organization': organization,
        'form': form,
        'document_rows': rows,
        'documents_uploaded': len([row for row in rows if row['document']]),
        'courses': organization.courses.all(),
    })
