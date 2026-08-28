from django.apps import AppConfig


class OrdersConfig(AppConfig):
    """App config for orders (customers, orders, stones)."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.orders"
