from django import forms

from core.forms import StyledFormMixin

from .models import Report, Review, ReviewReply


class ReviewForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {'rating': forms.RadioSelect}
        labels = {'rating': 'Your rating', 'comment': 'Your review'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Django adds an empty "---------" choice for drop-downs; as radio buttons only the 5 ratings make sense
        self.fields['rating'].choices = Review.RATING_CHOICES
        self.fields['comment'].widget.attrs['placeholder'] = 'What was good? What could be better?'


class ReplyForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ReviewReply
        fields = ['body']
        labels = {'body': 'Reply as your college'}
        # The reply box sits under each review without a visible label, so screen readers get this one
        widgets = {'body': forms.Textarea(attrs={'rows': 2, 'aria-label': 'Reply as your college',
                                                 'placeholder': 'Write a reply...'})}


class ReportForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Report
        fields = ['reason']
        labels = {'reason': 'What is wrong?'}
        help_texts = {'reason': 'For example: wrong tuition, a fake review, or abusive words.'}
