# accounts/urls.py
from django.urls import path
from .views import (
    RegisterView, VerifyEmailView, LoginView, 
    PasswordResetRequestView, PasswordResetConfirmView, 
    SupportContactView, UserProfileView, UserSettingsView 
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    path('login/', LoginView.as_view(), name='login'),
    path('password-reset/request/', PasswordResetRequestView.as_view(), name='pw-reset-request'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='pw-reset-confirm'),
    path('support/', SupportContactView.as_view(), name='support'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('settings/', UserSettingsView.as_view(), name='settings'),
]
