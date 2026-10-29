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
        return check_email_free(self.cleaned_data['email'])

    def clean(self):
        cleaned = super().clean()
        check_new_password(self, 'password', 'confirm_password')
        return cleaned


def check_email_free(email, user=None):
    """Form validation: emails are saved in lowercase and must not belong to another account."""
    email = email.lower()
    others = User.objects.filter(email=email)
    if user is not None:
        others = others.exclude(pk=user.pk)
    if others.exists():
        raise forms.ValidationError('An account with this email already exists.')
    return email


def check_new_password(form, field, confirm_field):
    """Form validation for a new password typed twice. Adds errors to the form."""
    password = form.cleaned_data.get(field)
    if password and password != form.cleaned_data.get(confirm_field):
        form.add_error(confirm_field, 'Passwords do not match.')
    elif password:
        # Django's built-in rules: minimum length, not too common, etc.
        try:
            validate_password(password)
        except forms.ValidationError as error:
            form.add_error(field, error)


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
    """The "Profile" settings tab. The photo and cover image come from core.forms.ImagesForm."""

    class Meta:
        model = UserProfile
        fields = ['bio', 'interests', 'hometown']
        labels = {'bio': 'About me'}
        help_texts = {'interests': 'For example: IT, nursing, business, arts.'}
        # Our text columns are TextFields, which show as big boxes; short values get a one-line input
        widgets = {'hometown': forms.TextInput}


class LocationForm(StyledFormMixin, forms.ModelForm):
    # The map under this field fills the hidden latitude and longitude (components/location_picker.html)
    map_after = 'address'

    class Meta:
        model = UserProfile
        fields = ['address', 'latitude', 'longitude', 'share_location']
        labels = {'share_location': 'Use my location to show distances to colleges'}
        help_texts = {'address': 'Search for a place or click the map to mark where you live.'}
        # Our text columns are TextFields, which show as big boxes; short values get a one-line input
        widgets = {'address': forms.TextInput, 'latitude': forms.HiddenInput, 'longitude': forms.HiddenInput}


class AccountForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ['full_name', 'email']
        # Our text columns are TextFields, which show as big boxes; short values get a one-line input
        widgets = {'full_name': forms.TextInput}

    def clean_email(self):
        return check_email_free(self.cleaned_data['email'], self.instance)


class PasswordForm(StyledFormMixin, forms.Form):
    current_password = forms.CharField(widget=forms.PasswordInput)
    new_password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput, label='Confirm new password')

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_current_password(self):
        password = self.cleaned_data['current_password']
        if not self.user.check_password(password):
            raise forms.ValidationError('This is not your current password.')
        return password

    def clean(self):
        cleaned = super().clean()
        check_new_password(self, 'new_password', 'confirm_password')
        return cleaned
