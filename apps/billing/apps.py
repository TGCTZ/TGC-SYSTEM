from django.apps import AppConfig


class BillingConfig(AppConfig):
    """App config for billing and GePG integration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.billing"
