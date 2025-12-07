# accounts/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User


# Optional: Custom forms (recommended for clean admin experience)
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'shop_name')


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = '__all__'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Forms to add and change user instances
    add_form = CustomUserCreationForm
    # When creating new user
    form = CustomUserChangeForm              # When editing existing user

    # Fields shown in the list view
    list_display = ('email', 'shop_name', 'is_email_verified', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_email_verified', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('email', 'shop_name')
    ordering = ('email',)

    # Fields shown when viewing/editing a user
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('shop_name', 'profile_picture', 'is_email_verified')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Fields shown when creating a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'shop_name', 'password1', 'password2', 'is_email_verified', 'is_staff', 'is_active')}
        ),
    )

    readonly_fields = ('date_joined', 'last_login')
    filter_horizontal = ('groups', 'user_permissions')