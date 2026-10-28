from django import forms

from core.forms import StyledFormMixin


class QuestionForm(StyledFormMixin, forms.Form):
    question = forms.CharField(
        max_length=500,
        label='Your question',
        widget=forms.Textarea(attrs={
            'rows': 2,
            'placeholder': 'e.g. Which IT course near me has good reviews and fits a ₱40,000 yearly budget?',
        }),
    )
