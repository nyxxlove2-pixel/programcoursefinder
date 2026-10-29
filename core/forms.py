from django import forms

from .uploads import check_image, image_field

# Tailwind classes for inputs, written once and shared by every form.
# Django adds aria-invalid="true" to fields with errors, so they turn red on their own.
# Phones get 16px text so iOS does not zoom in on focus; bigger screens use the tighter 14px.
INPUT_CLASSES = (
    'block min-h-[44px] w-full rounded-lg border border-slate-300 bg-slate-50 px-3.5 py-2.5 '
    'text-base text-ink transition placeholder:text-slate-400 hover:border-slate-400 sm:text-sm '
    'focus:border-transparent focus:bg-white focus:ring-2 focus:ring-indigo-600 '
    'aria-[invalid=true]:border-red-400 aria-[invalid=true]:bg-red-50/40 aria-[invalid=true]:focus:ring-red-500'
)
# Room on the right for the drop-down arrow
SELECT_CLASSES = INPUT_CLASSES + ' pr-10'
TEXTAREA_CLASSES = INPUT_CLASSES + ' resize-y leading-relaxed'
FILE_CLASSES = (
    'block w-full cursor-pointer rounded-lg border border-dashed border-slate-300 bg-slate-50 p-2 '
    'text-sm text-muted file:mr-4 file:cursor-pointer file:rounded-md file:border-0 file:bg-slate-900 '
    'file:px-4 file:py-2 file:text-sm file:font-semibold file:text-white hover:file:bg-slate-700'
)
CHECKBOX_CLASSES = 'h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-2 focus:ring-indigo-600'
RADIO_CLASSES = 'h-4 w-4 border-slate-300 text-indigo-600 focus:ring-2 focus:ring-indigo-600'


class StyledFormMixin:
    """Add our Tailwind styles to every field. Use it in any form:

        class MyForm(StyledFormMixin, forms.ModelForm): ...
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = classes_for(field.widget)
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.setdefault('rows', 4)


def classes_for(widget):
    """Pick the Tailwind classes that fit this kind of input."""
    # Radio buttons are drawn one by one in components/form_field.html, so this class lands on each circle
    if isinstance(widget, forms.RadioSelect):
        return RADIO_CLASSES
    if isinstance(widget, forms.CheckboxInput):
        return CHECKBOX_CLASSES
    if isinstance(widget, forms.FileInput):
        return FILE_CLASSES
    if isinstance(widget, forms.Select):
        return SELECT_CLASSES
    if isinstance(widget, forms.Textarea):
        return TEXTAREA_CLASSES
    return INPUT_CLASSES


class ImagesForm(forms.Form):
    """Photo (or logo) and cover image pickers for a profile, drawn by components/profile_images.html.
    Used next to the profile's own form in the same <form>; core/uploads.py saves the files."""

    photo = image_field('Photo', 'photo-preview')
    cover = image_field('Cover image', 'cover-preview')
    # Not a StyledFormMixin form (the file inputs stay hidden), so the checkboxes get their style here
    remove_photo = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': CHECKBOX_CLASSES}))
    remove_cover = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': CHECKBOX_CLASSES}))

    def clean_photo(self):
        return check_image(self.cleaned_data['photo'])

    def clean_cover(self):
        return check_image(self.cleaned_data['cover'])
