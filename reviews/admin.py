from django.contrib import admin

from .models import Report, Review

# There is no moderator role in the app. The developer checks reports
# here and deletes fake or abusive reviews.


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'reason', 'reporter', 'status', 'created_at']
    list_filter = ['status', 'target_type']
    readonly_fields = ['reporter', 'target_type', 'target_id', 'reason', 'created_at']
    actions = ['mark_resolved']

    @admin.action(description='Mark selected reports as resolved')
    def mark_resolved(self, request, queryset):
        queryset.update(status=Report.STATUS_RESOLVED)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['id', 'course', 'user', 'rating', 'created_at']
    search_fields = ['course__name', 'user__email', 'comment']
    readonly_fields = ['course', 'user', 'rating', 'comment', 'created_at']
