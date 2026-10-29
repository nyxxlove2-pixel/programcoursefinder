from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('settings/', views.edit_profile, name='settings'),
    path('settings/location/', views.edit_location, name='settings_location'),
    path('settings/account/', views.edit_account, name='settings_account'),
    path('settings/password/', views.change_password, name='settings_password'),
]
