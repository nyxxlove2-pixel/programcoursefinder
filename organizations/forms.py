from django import forms

from core.forms import StyledFormMixin

from .models import Organization, VerificationDocument

MAX_UPLOAD_MB = 10
ALLOWED_EXTENSIONS = ('.pdf', '.jpg', '.jpeg', '.png')


class OrganizationForm(StyledFormMixin, forms.ModelForm):
    # The map under this field fills the hidden latitude and longitude (components/location_picker.html)
    map_after = 'address'

    class Meta:
        model = Organization
        fields = [
            'name', 'description', 'phone', 'email', 'address',
            'latitude', 'longitude', 'website',
            'facebook_url', 'instagram_url', 'tiktok_url', 'youtube_url',
        ]
        labels = {'name': 'College / university name', 'email': 'Official email'}
        help_texts = {'address': 'Search for your campus or click the map to mark it.'}
        # Our text columns are TextFields, which show as big boxes; short values get a one-line input
        widgets = {
            'name': forms.TextInput, 'phone': forms.TextInput, 'address': forms.TextInput,
            'latitude': forms.HiddenInput, 'longitude': forms.HiddenInput,
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
