from django import forms

# Tailwind classes for inputs, written once and shared by every form.
# Django adds aria-invalid="true" to fields with errors, so they turn red on their own.
INPUT_CLASSES = (
    'block min-h-[48px] w-full rounded-xl border border-line bg-white px-4 py-3 text-ink shadow-sm '
    'transition placeholder:text-muted/60 hover:border-primary/40 '
    'focus:border-primary focus:ring-4 focus:ring-primary/15 '
    'aria-[invalid=true]:border-red-400 aria-[invalid=true]:focus:ring-red-100'
)
# Room on the right for the drop-down arrow
SELECT_CLASSES = INPUT_CLASSES + ' pr-10'
TEXTAREA_CLASSES = INPUT_CLASSES + ' resize-y leading-relaxed'
FILE_CLASSES = (
    'block w-full cursor-pointer rounded-xl border border-dashed border-primary/30 bg-lavender/50 p-2 '
    'text-sm text-muted file:mr-4 file:cursor-pointer file:rounded-full file:border-0 file:bg-primary '
    'file:px-5 file:py-2.5 file:font-semibold file:text-white hover:file:bg-primary-dark'
)
CHECKBOX_CLASSES = 'h-5 w-5 rounded-md border-line text-primary focus:ring-primary/30'
RADIO_CLASSES = 'h-4 w-4 border-line text-primary focus:ring-primary/30'


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
