from django.urls import path

from . import views

app_name = 'organizations'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('analytics/', views.analytics, name='analytics'),
    path('profile/', views.edit, name='edit'),
    path('documents/upload/', views.upload_document, name='upload_document'),
    path('documents/<int:pk>/', views.view_document, name='view_document'),
    path('<int:pk>/', views.detail, name='detail'),
]
