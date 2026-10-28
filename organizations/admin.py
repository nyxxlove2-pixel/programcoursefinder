from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Organization, VerificationDocument
from .utils import change_status, notify_status

# There is no administrator role in the app. The developer reviews
# organizations in the super admin dashboard (/superadmin/) or here.


class DocumentInline(admin.TabularInline):
    model = VerificationDocument
    fields = ['doc_type', 'open_file', 'uploaded_at', 'expires_at']
    readonly_fields = ['doc_type', 'open_file', 'uploaded_at']
    extra = 0
    can_delete = False

    @admin.display(description='File')
    def open_file(self, document):
        url = reverse('organizations:view_document', args=[document.pk])
        return format_html('<a href="{}" target="_blank">Open</a>', url)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'email', 'created_at']
    list_filter = ['status']
    search_fields = ['name', 'email']
    inlines = [DocumentInline]
    actions = ['approve', 'mark_needs_changes', 'reject']

    def save_model(self, request, organization, form, change):
        super().save_model(request, organization, form, change)
        if 'status' in form.changed_data or 'status_reason' in form.changed_data:
            notify_status(organization)

    def set_status(self, queryset, status):
        """Change the status of every selected organization and notify each one."""
        for organization in queryset:
            # Keep a reason already typed on the page, except when approving
            reason = '' if status == Organization.STATUS_APPROVED else organization.status_reason
            change_status(organization, status, reason)

    @admin.action(description='Approve selected organizations')
    def approve(self, request, queryset):
        self.set_status(queryset, Organization.STATUS_APPROVED)

    @admin.action(description='Mark as needs changes (add the reason on the page)')
    def mark_needs_changes(self, request, queryset):
        self.set_status(queryset, Organization.STATUS_NEEDS_CHANGES)

    @admin.action(description='Reject selected organizations')
    def reject(self, request, queryset):
        self.set_status(queryset, Organization.STATUS_REJECTED)
