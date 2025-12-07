# accounts/utils.py
import random
from django.core.mail import send_mail
from django.conf import settings


def generate_code(n=6):
    """
    Generate a numeric verification code of length n (default 6).
    """
    return ''.join(str(random.randint(0, 9)) for _ in range(n))


def send_verification_email(email, code):
    """
    Send a verification code to the specified email.
    """
    subject = 'Your verification code'
    message = f'Your verification code is: {code}\n\nThis code will expire in 15 minutes.'
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False
    )


def send_support_email(subject, body, from_email=None):
    """
    Send support emails to the default support inbox.
    """
    send_mail(
        subject,
        body,
        from_email or settings.DEFAULT_FROM_EMAIL,
        [settings.DEFAULT_FROM_EMAIL],
        fail_silently=False
    )