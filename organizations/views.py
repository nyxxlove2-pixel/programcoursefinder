from django.contrib import messages
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import User
from accounts.utils import get_current_user, role_required
from courses.utils import add_distances, get_compare_ids, public_courses, user_location, with_ratings
from reviews.models import Review
from reviews.utils import (
    add_reaction_counts, monthly_trend, organization_review_stats, rating_distribution,
)

from .forms import DocumentForm, OrganizationForm
from .models import Organization, VerificationDocument
from .utils import document_rows, get_own_organization


@role_required(User.ROLE_ORGANIZATION)
def dashboard(request):
    organization = get_own_organization(request.app_user)
    if organization is None:
        messages.info(request, 'First, set up your college profile.')
        return redirect('organizations:edit')

    rows = document_rows(organization)
    uploaded = len([row for row in rows if row['document']])
    return render(request, 'organizations/dashboard.html', {
        'organization': organization,
        'document_rows': rows,
        'documents_uploaded': uploaded,
        'documents_percent': uploaded * 100 // len(rows),
        'courses': add_reaction_counts(with_ratings(organization.courses.all())),
        'review_stats': organization_review_stats(organization),
    })


@role_required(User.ROLE_ORGANIZATION)
def analytics(request):
    """Trends and per-course numbers, all worked out from the college's reviews."""
    organization = get_own_organization(request.app_user)
    if organization is None:
        return redirect('organizations:edit')

    reviews = Review.objects.filter(course__organization=organization)
    stats = organization_review_stats(organization)
    answered = stats['review_count'] - stats['needs_reply']
    courses = add_reaction_counts(with_ratings(organization.courses.all()))
    # Best-rated first; courses without reviews go last
    courses.sort(key=lambda c: (c.average_rating is None, -(c.average_rating or 0)))
    trend = monthly_trend(reviews)
    return render(request, 'organizations/analytics.html', {
        'stats': stats,
        'reply_rate': answered * 100 // stats['review_count'] if stats['review_count'] else None,
        'trend': trend,
        'reviews_last_year': sum(month['count'] for month in trend),
        'distribution': rating_distribution(reviews),
        'courses': courses,
    })


@role_required(User.ROLE_ORGANIZATION)
def edit(request):
    organization = get_own_organization(request.app_user)
    form = OrganizationForm(request.POST or None, instance=organization)
    if request.method == 'POST' and form.is_valid():
        organization = form.save(commit=False)
        organization.owner = request.app_user
        organization.save()
        messages.success(request, 'College profile saved.')
        return redirect('organizations:dashboard')
    return render(request, 'organizations/edit.html', {'form': form})


@role_required(User.ROLE_ORGANIZATION)
def upload_document(request):
    organization = get_own_organization(request.app_user)
    if organization is None:
        return redirect('organizations:edit')

    form = DocumentForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        # Replace the old file if this document type was uploaded before
        document = VerificationDocument.objects.filter(
            organization=organization, doc_type=form.cleaned_data['doc_type']
        ).first() or VerificationDocument(
            organization=organization, doc_type=form.cleaned_data['doc_type']
        )
        document.file = form.cleaned_data['file']
        document.save()

        # New documents need a fresh review
        if organization.status in (Organization.STATUS_NEEDS_CHANGES, Organization.STATUS_REJECTED):
            organization.status = Organization.STATUS_PENDING
            organization.save()

        messages.success(request, 'Document uploaded.')
        return redirect('organizations:dashboard')
    return render(request, 'organizations/upload_document.html', {'form': form})


def view_document(request, pk):
    # Documents are private: only the owning organization or the
    # developer (logged into Django admin) can open them.
    document = get_object_or_404(VerificationDocument, pk=pk)
    current_user = get_current_user(request)
    is_owner = current_user is not None and document.organization.owner_id == current_user.id
    if not (is_owner or request.user.is_staff):
        raise Http404
    return FileResponse(document.file.open('rb'))


def detail(request, pk):
    # Public college page. Only verified colleges are shown.
    organization = get_object_or_404(
        Organization, pk=pk, status=Organization.STATUS_APPROVED
    )
    return render(request, 'organizations/detail.html', {
        'organization': organization,
        'courses': add_distances(
            public_courses().filter(organization=organization), user_location(request)
        ),
        'compare_ids': get_compare_ids(request),
    })
