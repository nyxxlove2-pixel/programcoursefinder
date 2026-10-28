from django.urls import path

from . import views

app_name = 'ads'

urlpatterns = [
    path('', views.ad_list, name='list'),
    path('<int:pk>/delete/', views.delete, name='delete'),
]
