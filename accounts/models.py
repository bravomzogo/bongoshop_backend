# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
import cloudinary.models  # If using Cloudinary

class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    shop_name = models.CharField(max_length=150)
    
    # Use CloudinaryField for image uploads (recommended)
    profile_picture = cloudinary.models.CloudinaryField(
        'profile_pictures',
        folder='bongoshop/profiles/',
        blank=True,
        null=True,
        transformation=[
            {'width': 300, 'height': 300, 'crop': 'fill'},
            {'quality': 'auto:good'}
        ]
    )
    
    # OR if you want to use local file storage:
    # profile_picture = models.ImageField(
    #     upload_to='profile_pictures/',
    #     blank=True,
    #     null=True,
    #     max_length=500
    # )
    
    is_email_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email