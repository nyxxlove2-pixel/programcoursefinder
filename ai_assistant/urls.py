from django.urls import path

from . import views

app_name = 'ai_assistant'

urlpatterns = [
    path('', views.assistant, name='assistant'),
    path('<int:pk>/', views.assistant, name='conversation'),
    path('<int:pk>/delete/', views.delete_conversation, name='delete_conversation'),
    path('translate/<int:pk>/', views.translate_review, name='translate_review'),
    path('summaries/', views.summaries, name='summaries'),
    path('summaries/<int:course_pk>/<str:period_type>/generate/', views.generate_summary, name='generate_summary'),
]
