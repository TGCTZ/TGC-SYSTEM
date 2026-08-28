"""Register models with django-auditlog for change-history tracking."""

from auditlog.registry import auditlog
from django.apps import apps
from django.contrib.auth import get_user_model

from apps.core.models import BaseModel

# Columns already captured by BaseModel/auditlog itself — kept out of the diff
# to reduce noise. deleted_at stays tracked so soft deletes appear as changes.
_EXCLUDED = ["created_at", "updated_at", "created_by", "updated_by", "deleted_by"]


def register_audit_models():
    """Register every concrete BaseModel subclass, plus User, with auditlog."""
    for model in apps.get_models():
        if issubclass(model, BaseModel) and not model._meta.abstract:
            auditlog.register(model, exclude_fields=_EXCLUDED)
    auditlog.register(get_user_model(), exclude_fields=["password", "last_login"])
