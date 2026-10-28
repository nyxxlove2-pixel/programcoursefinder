from django import forms

from core.forms import StyledFormMixin

from .models import Organization, VerificationDocument

MAX_UPLOAD_MB = 10
ALLOWED_EXTENSIONS = ('.pdf', '.jpg', '.jpeg', '.png')


class OrganizationForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Organization
        fields = [
            'name', 'description', 'phone', 'email', 'address',
            'latitude', 'longitude', 'website',
            'facebook_url', 'instagram_url', 'tiktok_url', 'youtube_url',
        ]
        labels = {'name': 'College / university name', 'email': 'Official email'}
        help_texts = {
            'latitude': 'Tip: right-click your campus on Google Maps to copy the numbers.',
        }


class DocumentForm(StyledFormMixin, forms.Form):
    doc_type = forms.ChoiceField(
        choices=VerificationDocument.DOC_TYPE_CHOICES, label='Document type'
    )
    file = forms.FileField(help_text=f'PDF, JPG, or PNG. Max {MAX_UPLOAD_MB} MB.')

    def clean_file(self):
        file = self.cleaned_data['file']
        if not file.name.lower().endswith(ALLOWED_EXTENSIONS):
            raise forms.ValidationError('Only PDF, JPG, or PNG files are allowed.')
        if file.size > MAX_UPLOAD_MB * 1024 * 1024:
            raise forms.ValidationError(f'File is larger than {MAX_UPLOAD_MB} MB.')
        return file
