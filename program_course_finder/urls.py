from django.contrib import admin
from django.urls import include, path

# Uploaded files are NOT served publicly on purpose: verification
# documents are private and go through organizations:view_document.
urlpatterns = [
    path('admin/', admin.site.urls),
    path('superadmin/', include('superadmin.urls')),
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    path('organizations/', include('organizations.urls')),
    path('courses/', include('courses.urls')),
    path('reviews/', include('reviews.urls')),
    path('notifications/', include('notifications.urls')),
    path('assistant/', include('ai_assistant.urls')),
    path('ads/', include('ads.urls')),
]
