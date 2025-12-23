"""
Assets App Configuration
Django app configuration for the Asset Management system
"""

from django.apps import AppConfig


class AssetsConfig(AppConfig):
    """Configuration for the assets app"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "assets"
    verbose_name = "Asset Management"
