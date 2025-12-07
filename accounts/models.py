# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    username = None  # we will use email as unique identifier
    email = models.EmailField(unique=True)
    shop_name = models.CharField(max_length=150)
    profile_picture = models.URLField(blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email