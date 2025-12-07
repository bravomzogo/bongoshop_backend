# accounts/management/commands/createsuperuser.py

from django.contrib.auth import get_user_model
from django.contrib.auth.management.commands.createsuperuser import Command as BaseCommand
from django.core.management.base import CommandError

User = get_user_model()

class Command(BaseCommand):
    help = "Create a superuser using email instead of username"

    def handle(self, *args, **options):
        # Force interactive mode to ask for email
        if options['interactive']:
            email = None
            while not email:
                email = input("Email address: ").strip()
                if not email:
                    self.stderr.write("Error: Email cannot be empty.")
            
            # Set email as the username field (since USERNAME_FIELD = 'email')
            options[User.USERNAME_FIELD] = email
            # Also set username to be safe
            options['email'] = email

            # Ask for shop_name if it's required
            if 'shop_name' in [f.name for f in User._meta.get_fields()]:
                shop_name = input("Shop name (optional, press Enter to skip): ").strip()
                if shop_name:
                    options['shop_name'] = shop_name or "Admin Shop"

        return super().handle(*args, **options)