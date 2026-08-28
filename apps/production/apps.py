from django.apps import AppConfig


class ProductionConfig(AppConfig):
    """App config for production (sonara, carving, lapidary)."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.production"
