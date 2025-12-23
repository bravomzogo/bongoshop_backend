# accounts/serializers.py
from rest_framework import serializers
from .models import User
from django.contrib.auth.password_validation import validate_password
from django.core.validators import EmailValidator
import re


class UserUpdateSerializer(serializers.ModelSerializer):
    current_password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    new_password = serializers.CharField(write_only=True, required=False, allow_blank=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = ('shop_name', 'email', 'current_password', 'new_password', 'confirm_password', 'profile_picture')
        extra_kwargs = {
            'shop_name': {'required': False},
            'email': {'required': False},
            'profile_picture': {'required': False, 'allow_null': True}
        }
    
    def validate(self, data):
        # Check if passwords are provided
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        current_password = data.get('current_password')
        
        if new_password or confirm_password:
            # Both password fields must be provided
            if not (new_password and confirm_password):
                raise serializers.ValidationError(
                    "Both new password and confirm password are required for password change"
                )
            
            # Check if current password is provided for password change
            if not current_password:
                raise serializers.ValidationError(
                    "Current password is required to change password"
                )
            
            # Check if new passwords match
            if new_password != confirm_password:
                raise serializers.ValidationError(
                    "New password and confirm password do not match"
                )
        
        return data
    
    def update(self, instance, validated_data):
        # Remove password fields from validated_data
        current_password = validated_data.pop('current_password', None)
        new_password = validated_data.pop('new_password', None)
        validated_data.pop('confirm_password', None)
        
        # Check if user wants to change password
        if new_password and current_password:
            # Verify current password
            if not instance.check_password(current_password):
                raise serializers.ValidationError(
                    {"current_password": ["Current password is incorrect"]}
                )
            
            # Set new password
            instance.set_password(new_password)
        
        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class UserSerializer(serializers.ModelSerializer):
    profile_picture_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'shop_name', 'email', 'profile_picture_url', 'is_email_verified')
    
    def get_profile_picture_url(self, obj):
        if obj.profile_picture:
            # Return full URL if using Cloudinary or similar
            if hasattr(obj.profile_picture, 'url'):
                return obj.profile_picture.url
            return str(obj.profile_picture)
        return None


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    
    class Meta:
        model = User
        fields = ('id', 'shop_name', 'email', 'profile_picture', 'password')
        extra_kwargs = {
            'profile_picture': {'required': False, 'allow_null': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.is_active = True
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)