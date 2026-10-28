from django import forms
from django.contrib.auth.password_validation import validate_password

from core.forms import StyledFormMixin

from .models import User, UserProfile


class RegisterForm(StyledFormMixin, forms.Form):
    full_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        label='I am registering as',
        widget=forms.RadioSelect,
    )
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        if password and password != cleaned.get('confirm_password'):
            self.add_error('confirm_password', 'Passwords do not match.')
        elif password:
            # Django's built-in rules: minimum length, not too common, etc.
            try:
                validate_password(password)
            except forms.ValidationError as error:
                self.add_error('password', error)
        return cleaned


class LoginForm(StyledFormMixin, forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get('email', '').lower()
        user = User.objects.filter(email=email).first()
        # Same message for both cases so we don't reveal which emails exist
        if user is None or not user.check_password(cleaned.get('password', '')):
            raise forms.ValidationError('Wrong email or password.')
        cleaned['user'] = user
        return cleaned


class ProfileForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'interests', 'bio', 'hometown', 'address',
            'latitude', 'longitude', 'share_location',
        ]
        labels = {'share_location': 'Use my location to show distances to colleges'}
        help_texts = {
            'latitude': 'Tip: right-click your home on Google Maps to copy the numbers.',
        }
