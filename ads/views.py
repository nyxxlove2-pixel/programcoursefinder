from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import User
from accounts.utils import role_required
from organizations.utils import get_own_organization

from .forms import AdForm


@role_required(User.ROLE_ORGANIZATION)
def ad_list(request):
    """The college's ads, with the form to submit a new one on the same page."""
    organization = get_own_organization(request.app_user)
    if organization is None:
        return redirect('organizations:edit')

    form = AdForm(request.POST or None, organization=organization)
    if request.method == 'POST' and form.is_valid():
        ad = form.save(commit=False)
        ad.organization = organization
        ad.save()
        messages.success(request, 'Ad sent for review. It goes live once approved.')
        return redirect('ads:list')
    return render(request, 'ads/list.html', {
        'form': form,
        'ads': organization.ads.select_related('course'),
        'organization': organization,
    })


@role_required(User.ROLE_ORGANIZATION)
@require_POST
def delete(request, pk):
    organization = get_own_organization(request.app_user)
    ad = get_object_or_404(organization.ads, pk=pk)
    ad.delete()
    messages.success(request, 'Ad removed.')
    return redirect('ads:list')
