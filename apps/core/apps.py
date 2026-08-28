from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"

    def ready(self):
        """Register all CRUD models with auditlog once apps are loaded."""
        from apps.core.audit import register_audit_models

        register_audit_models()
