from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from core.forms import ImagesForm
from core.uploads import UPLOAD_FAILED_MESSAGE, UploadFailed, delete_if_replaced, new_image_url

from .forms import AccountForm, LocationForm, LoginForm, PasswordForm, ProfileForm, RegisterForm
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
    """The user's own profile page: cover image, photo, and details."""
    user_profile, _ = UserProfile.objects.get_or_create(user=request.app_user)
    return render(request, 'accounts/profile.html', {'profile': user_profile})


# ---------- Settings (one page per tab, see components/settings_tabs.html) ----------

@role_required(User.ROLE_USER)
def edit_profile(request):
    user_profile, _ = UserProfile.objects.get_or_create(user=request.app_user)
    form = ProfileForm(request.POST or None, instance=user_profile)
    images = ImagesForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid() and images.is_valid():
        if save_profile(request, form, images):
            messages.success(request, 'Profile saved.')
            return redirect('accounts:profile')
    return render(request, 'accounts/settings_profile.html', {'form': form, 'images': images, 'profile': user_profile})


def save_profile(request, form, images):
    """Save the profile details, photo, and cover image.
    Returns False (with an error message) when an image could not be uploaded."""
    user = request.app_user
    user_profile = form.save(commit=False)
    old_photo, old_cover = user.avatar_url, user_profile.cover_url
    folder = f'users/{user.pk}'
    try:
        user.avatar_url = new_image_url(images, 'photo', old_photo, folder)
        user_profile.cover_url = new_image_url(images, 'cover', old_cover, folder)
    except UploadFailed:
        messages.error(request, UPLOAD_FAILED_MESSAGE)
        return False
    user.save(update_fields=['avatar_url'])
    user_profile.save()
    delete_if_replaced(old_photo, user.avatar_url)
    delete_if_replaced(old_cover, user_profile.cover_url)
    return True


@role_required(User.ROLE_USER)
def edit_location(request):
    user_profile, _ = UserProfile.objects.get_or_create(user=request.app_user)
    form = LocationForm(request.POST or None, instance=user_profile)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Location saved.')
        return redirect('accounts:settings_location')
    return render(request, 'accounts/settings_location.html', {'form': form})


@role_required()
def edit_account(request):
    form = AccountForm(request.POST or None, instance=request.app_user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Account details saved.')
        return redirect('accounts:settings_account')
    return render(request, 'accounts/settings_account.html', {'form': form})


@role_required()
def change_password(request):
    form = PasswordForm(request.app_user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        request.app_user.set_password(form.cleaned_data['new_password'])
        request.app_user.save(update_fields=['password_hash'])
        messages.success(request, 'Password changed.')
        return redirect('accounts:settings_password')
    return render(request, 'accounts/settings_password.html', {'form': form})
