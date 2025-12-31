from django.contrib.auth.models import BaseUserManager
# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
import cloudinary.models  # If using Cloudinary


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)




class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    shop_name = models.CharField(max_length=150)

    profile_picture = cloudinary.models.CloudinaryField(
        'profile_pictures',
        folder='bongoshop/profiles/',
        blank=True,
        null=True,
    )

    is_email_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()  # 👈 THIS LINE IS CRITICAL

    def __str__(self):
        return self.email
