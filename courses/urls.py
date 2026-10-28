from django.urls import path

from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.search, name='search'),
    path('<int:pk>/', views.detail, name='detail'),
    path('compare/', views.compare, name='compare'),
    path('compare/<int:pk>/', views.compare_toggle, name='compare_toggle'),
    path('new/', views.course_form, name='add'),
    path('upload/', views.bulk_upload, name='bulk_upload'),
    path('upload/template.csv', views.csv_template, name='csv_template'),
    path('<int:pk>/edit/', views.course_form, name='edit'),
    path('<int:pk>/delete/', views.delete, name='delete'),
]
