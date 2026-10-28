from django import forms

from core.forms import StyledFormMixin

from .models import Ad, youtube_id


class AdForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Ad
        fields = ['title', 'ad_type', 'media_url', 'course']
        widgets = {'ad_type': forms.RadioSelect}
        labels = {
            'title': 'Ad headline',
            'ad_type': 'Ad type',
            'media_url': 'Image or video link',
            'course': 'Link to course (optional)',
        }
        help_texts = {
            'media_url': 'Banner: a direct link to a wide image (about 1200 × 300). Video: a YouTube link.',
            'course': 'Leave empty to link to your college page.',
        }

    def __init__(self, *args, organization, **kwargs):
        super().__init__(*args, **kwargs)
        # Colleges can only advertise their own courses
        self.fields['course'].queryset = organization.courses.all()
        self.fields['course'].empty_label = 'My college page'

    def clean(self):
        cleaned_data = super().clean()
        is_video = cleaned_data.get('ad_type') == Ad.TYPE_VIDEO
        if is_video and not youtube_id(cleaned_data.get('media_url')):
            self.add_error('media_url', 'Enter a YouTube link, like https://youtu.be/abc123XYZ00')
        return cleaned_data
