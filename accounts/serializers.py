# accounts/serializers.py
from rest_framework import serializers
from .models import User
from django.contrib.auth.password_validation import validate_password


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    profile_picture = serializers.ImageField(required=False, allow_null=True)  # Accept image file

    class Meta:
        model = User
        fields = ('id', 'shop_name', 'email', 'profile_picture', 'password')

    def create(self, validated_data):
        password = validated_data.pop('password')
        profile_picture = validated_data.pop('profile_picture', None)

        user = User(**validated_data)
        user.set_password(password)
        user.is_active = True

        if profile_picture:
            user.profile_picture = profile_picture  # Cloudinary will handle URL

        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'shop_name', 'email', 'profile_picture', 'is_email_verified')
