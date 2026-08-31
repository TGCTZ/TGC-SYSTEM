from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules


class AdminPanelConfig(AppConfig):
    """The generic model-admin framework.

    On startup it autodiscovers each app's ``panels.py`` (Django-admin style), so
    models register themselves with the panel registry.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.adminpanel"

    def ready(self):
        """Import every app's ``panels`` module to populate the registry."""
        autodiscover_modules("panels")
