"""Profile photos, logos, and cover images, stored in Supabase Storage.

Vercel's disk is read-only, so uploaded images cannot be saved next to the code.
Settings: SUPABASE_URL and SUPABASE_SERVICE_KEY in .env.
"""
import logging
import urllib.request
import uuid

from django import forms
from django.conf import settings

BUCKET = 'profile-images'
MAX_IMAGE_MB = 5
# Allowed image types and the file extension we save each one with
IMAGE_TYPES = {'image/jpeg': 'jpg', 'image/png': 'png', 'image/webp': 'webp'}
UPLOAD_FAILED_MESSAGE = 'The image could not be uploaded. Please try again in a minute.'

logger = logging.getLogger(__name__)


class UploadFailed(Exception):
    """Supabase Storage could not save the image."""


def image_field(label, preview_id):
    """An optional image picker. preview_id is the <img> that shows the picked file
    before saving (see components/profile_images.html)."""
    return forms.FileField(
        required=False,
        label=label,
        widget=forms.FileInput(attrs={'accept': ','.join(IMAGE_TYPES), 'class': 'sr-only', 'data-preview': preview_id}),
    )


def check_image(file):
    """Form validation for a picked image: the right type and not too big. No file is fine."""
    if not file:
        return file
    if file.content_type not in IMAGE_TYPES:
        raise forms.ValidationError('Use a JPG, PNG, or WebP image.')
    if file.size > MAX_IMAGE_MB * 1024 * 1024:
        raise forms.ValidationError(f'The image is larger than {MAX_IMAGE_MB} MB.')
    return file


def storage_request(path, method, data=None, content_type=None):
    """Send one request to the Supabase Storage API for a file in our bucket."""
    headers = {
        'Authorization': f'Bearer {settings.SUPABASE_SERVICE_KEY}',
        'apikey': settings.SUPABASE_SERVICE_KEY,
    }
    if content_type:
        headers['Content-Type'] = content_type
    url = f'{settings.SUPABASE_URL}/storage/v1/object/{BUCKET}/{path}'
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    urllib.request.urlopen(request, timeout=20)


def public_prefix():
    return f'{settings.SUPABASE_URL}/storage/v1/object/public/{BUCKET}/'


def upload_image(file, folder):
    """Save the image under folder/ and return its public link. Raises UploadFailed."""
    if not (settings.SUPABASE_URL and settings.SUPABASE_SERVICE_KEY):
        logger.warning('Image upload skipped: SUPABASE_URL and SUPABASE_SERVICE_KEY are not set.')
        raise UploadFailed('Supabase Storage is not set up.')
    # A new random name each time, so browsers never show an old cached image
    path = f'{folder}/{uuid.uuid4().hex}.{IMAGE_TYPES[file.content_type]}'
    try:
        storage_request(path, 'POST', data=file.read(), content_type=file.content_type)
    except OSError as error:  # network problems and HTTP errors are both OSErrors
        logger.warning('Supabase Storage upload failed: %s', error)
        raise UploadFailed(str(error)) from error
    return public_prefix() + path


def delete_image(url):
    """Remove an image we stored earlier. If it fails we only leave an unused file, so errors are ignored."""
    if not url or not url.startswith(public_prefix()):
        return
    try:
        storage_request(url.removeprefix(public_prefix()), 'DELETE')
    except OSError:
        pass


def new_image_url(images_form, name, current_url, folder):
    """The link to save for one image of an ImagesForm: a fresh upload, None when
    "remove" is ticked, or the current link when nothing changed. Raises UploadFailed."""
    file = images_form.cleaned_data.get(name)
    if file:
        return upload_image(file, folder)
    if images_form.cleaned_data.get(f'remove_{name}'):
        return None
    return current_url


def delete_if_replaced(old_url, new_url):
    """Call after saving: deletes the old image when it was replaced or removed."""
    if old_url != new_url:
        delete_image(old_url)
