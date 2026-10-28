from django.contrib import admin

from .models import Course


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'yearly_tuition', 'last_updated']
    search_fields = ['name', 'organization__name']
