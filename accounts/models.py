from django.contrib.auth.hashers import check_password, make_password
from django.db import models


# These models map to tables that already exist in Supabase
# (see Program_Course_Finder_Schema.sql), so managed = False tells
# Django not to create or change them.


class User(models.Model):
    ROLE_USER = 'user'
    ROLE_ORGANIZATION = 'organization'
    ROLE_CHOICES = [
        (ROLE_USER, 'User'),
        (ROLE_ORGANIZATION, 'Organization'),
    ]

    email = models.EmailField(unique=True)
    password_hash = models.TextField()
    full_name = models.TextField()
    role = models.TextField(choices=ROLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'users'

    def __str__(self):
        return self.email

    def set_password(self, raw_password):
        # Never store the real password, only a secure hash of it
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password_hash)

    @property
    def is_organization(self):
        return self.role == self.ROLE_ORGANIZATION


class UserProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, primary_key=True, related_name='profile'
    )
    interests = models.TextField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    hometown = models.TextField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    share_location = models.BooleanField(default=False)

    class Meta:
        managed = False
        db_table = 'user_profiles'

    def location(self):
        """Return (lat, lng) only if the user agreed to share it."""
        if self.share_location and self.latitude and self.longitude:
            return (self.latitude, self.longitude)
        return None
