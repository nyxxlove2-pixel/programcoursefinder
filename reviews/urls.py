from django.urls import path

from . import views

app_name = 'reviews'

urlpatterns = [
    path('course/<int:course_pk>/', views.save_review, name='save'),
    path('<int:pk>/react/', views.react, name='react'),
    path('<int:pk>/reply/', views.reply, name='reply'),
    path('report/<str:target_type>/<int:target_id>/', views.report, name='report'),
    path('mine/', views.organization_reviews, name='organization_reviews'),
]
