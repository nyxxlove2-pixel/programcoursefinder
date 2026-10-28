from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import LoginForm, ProfileForm, RegisterForm
from .models import User, UserProfile
from .utils import log_in, log_out, redirect_home, role_required


def register(request):
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        data = form.cleaned_data
        user = User(full_name=data['full_name'], email=data['email'], role=data['role'])
        user.set_password(data['password'])
        user.save()
        if not user.is_organization:
            UserProfile.objects.create(user=user)
        log_in(request, user)
        messages.success(request, f'Welcome, {user.full_name}!')
        return redirect_home(user)
    return render(request, 'accounts/register.html', {'form': form})


def login(request):
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.cleaned_data['user']
        log_in(request, user)
        return redirect_home(user)
    return render(request, 'accounts/login.html', {'form': form})


@require_POST
def logout(request):
    log_out(request)
    messages.info(request, 'You have been logged out.')
    return redirect('core:home')


@role_required(User.ROLE_USER)
def profile(request):
    user_profile, _ = UserProfile.objects.get_or_create(user=request.app_user)
    form = ProfileForm(request.POST or None, instance=user_profile)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Profile saved.')
        return redirect('accounts:profile')
    return render(request, 'accounts/profile.html', {'form': form})
