from django import forms
from django.core.validators import FileExtensionValidator

from core.forms import StyledFormMixin
from organizations.models import Organization

from .models import Course
from .utils import SORT_CHOICES


class CourseForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name', 'description', 'yearly_tuition', 'term_tuition']
        labels = {
            'name': 'Course / program name',
            'yearly_tuition': 'Yearly tuition',
            'term_tuition': 'Per-term tuition',
        }
        help_texts = {
            'description': 'What students learn, how long it takes, and any entry requirements.',
            'term_tuition': 'Optional. Leave empty if you only charge per year.',
        }
        widgets = {'description': forms.Textarea(attrs={'rows': 5})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['placeholder'] = 'e.g. BS Nursing'
        self.fields['description'].widget.attrs['placeholder'] = 'A short overview students will read first'
        # Room on the left for the ₱ sign drawn by components/form_field.html
        for name, example in [('yearly_tuition', '40000'), ('term_tuition', '20000')]:
            self.fields[name].widget.attrs['class'] += ' pl-9'
            self.fields[name].widget.attrs['placeholder'] = example


class CourseUploadForm(StyledFormMixin, forms.Form):
    file = forms.FileField(
        label='CSV file',
        validators=[FileExtensionValidator(['csv'])],
        help_text='Columns: name, description, yearly_tuition, term_tuition. Max 200 rows.',
    )


class SearchForm(StyledFormMixin, forms.Form):
    # The field names match the arguments of courses.utils.search_courses
    query = forms.CharField(required=False, label='Course or college')
    college = forms.ModelChoiceField(
        queryset=Organization.objects.filter(status=Organization.STATUS_APPROVED).order_by('name'),
        required=False,
        empty_label='All colleges',
    )
    min_tuition = forms.DecimalField(required=False, min_value=0, label='Min (₱)')
    max_tuition = forms.DecimalField(required=False, min_value=0, label='Max (₱)')
    max_distance = forms.IntegerField(required=False, min_value=1, label='Within (km)')
    sort = forms.ChoiceField(choices=SORT_CHOICES, required=False, label='Sort by')

    FILTER_FIELDS = ['college', 'min_tuition', 'max_tuition', 'max_distance']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # The filters sit beside the results, outside the <form> tag,
        # so each field points to the form by its id instead.
        for field in self.fields.values():
            field.widget.attrs['form'] = 'course-search'
        self.fields['query'].widget.attrs['placeholder'] = 'Search a course or college, e.g. Nursing'
        # A bigger pill for the main search bar, with room for the search icon
        self.fields['query'].widget.attrs['class'] += ' rounded-full py-4 pl-12 text-base'
        # Re-run the search as soon as a new sort order is picked
        self.fields['sort'].widget.attrs['onchange'] = 'this.form.submit()'

    def active_filter_count(self):
        """How many filters (not counting the search words or sort) are in use."""
        if not self.is_bound or not self.is_valid():
            return 0
        used = [name for name in self.FILTER_FIELDS if self.cleaned_data.get(name) is not None]
        return len(used)
