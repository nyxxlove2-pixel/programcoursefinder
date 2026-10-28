from django import forms

from core.forms import StyledFormMixin
from organizations.models import Organization


class DecisionForm(StyledFormMixin, forms.Form):
    DECISION_CHOICES = [
        (Organization.STATUS_APPROVED, 'Approve'),
        (Organization.STATUS_NEEDS_CHANGES, 'Needs changes'),
        (Organization.STATUS_REJECTED, 'Reject'),
    ]

    decision = forms.ChoiceField(choices=DECISION_CHOICES, widget=forms.RadioSelect, label='Decision')
    reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'e.g. The SEC registration is expired. Please upload the latest one.'}),
        label='Message to the college',
        help_text='Required for "Needs changes" and "Reject". The college sees it on its dashboard.',
    )

    def clean(self):
        cleaned_data = super().clean()
        decision = cleaned_data.get('decision')
        if decision and decision != Organization.STATUS_APPROVED and not cleaned_data.get('reason'):
            self.add_error('reason', 'Tell the college what to fix.')
        return cleaned_data
