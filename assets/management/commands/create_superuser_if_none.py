"""
Django management command to create superuser if none exists.
This runs automatically on container startup (see docker-compose.yml).

Reads credentials from environment variables:
- DJANGO_SUPERUSER_USERNAME
- DJANGO_SUPERUSER_PASSWORD
- DJANGO_SUPERUSER_EMAIL
"""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create superuser if no users exist (auto-setup from environment)"

    def handle(self, *args, **options):
        User = get_user_model()

        # Check if any users exist
        if User.objects.exists():
            self.stdout.write(
                self.style.SUCCESS("Users already exist. Skipping superuser creation.")
            )
            return

        # Get credentials from environment
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "admin")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@example.com")

        # Create superuser
        try:
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
            )
            self.stdout.write(
                self.style.SUCCESS(f"✓ Superuser '{username}' created successfully!")
            )
            self.stdout.write(
                self.style.WARNING(
                    f"  Login at http://localhost:8000/admin/ or http://localhost:8000/login/"
                )
            )
            self.stdout.write(self.style.WARNING(f"  Username: {username}"))
            self.stdout.write(self.style.WARNING(f"  Password: {password}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to create superuser: {str(e)}"))
