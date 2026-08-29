from django.apps import AppConfig


class DashboardConfig(AppConfig):
    """App config for the dashboard shell, navigation, and styleguide."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.dashboard"
