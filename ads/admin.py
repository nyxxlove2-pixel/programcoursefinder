from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from notifications.utils import notify

from .models import Ad

# The developer checks every ad here before it goes live.


@admin.register(Ad)
class AdAdmin(admin.ModelAdmin):
    list_display = ['title', 'organization', 'ad_type', 'preview', 'status', 'created_at']
    list_filter = ['status', 'ad_type']
    actions = ['approve', 'reject']

    @admin.display(description='Media')
    def preview(self, ad):
        return format_html('<a href="{}" target="_blank" rel="noopener">Open</a>', ad.media_url)

    def set_status(self, queryset, status):
        """Update the selected ads and tell each college."""
        queryset.update(status=status)
        for ad in queryset.select_related('organization__owner'):
            notify(ad.organization.owner, f'Your ad "{ad.title}" was {ad.get_status_display().lower()}.', reverse('ads:list'))

    @admin.action(description='Approve selected ads')
    def approve(self, request, queryset):
        self.set_status(queryset, Ad.STATUS_APPROVED)

    @admin.action(description='Reject selected ads')
    def reject(self, request, queryset):
        self.set_status(queryset, Ad.STATUS_REJECTED)
