"""Abstract base model: audit columns + soft delete.

Every CRUD model inherits this. Actor fields (created_by/updated_by/deleted_by)
are set by the service layer, since models don't know the request user.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.managers import SoftDeleteManager


class BaseModel(models.Model):
    """Abstract base with audit columns and soft delete. Inherited by all CRUD models."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",  # no reverse accessor — actor links aren't queried backwards
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    objects = SoftDeleteManager()  # live rows only (default)
    all_objects = models.Manager()  # includes soft-deleted, for admin/audit

    class Meta:
        abstract = True

    @property
    def is_deleted(self) -> bool:
        """True if the row is soft-deleted."""
        return self.deleted_at is not None

    def delete(self, using=None, keep_parents=False):
        """Soft delete: stamp deleted_at instead of removing the row."""
        self.deleted_at = timezone.now()
        self.save(using=using, update_fields=["deleted_at", "updated_at"])

    def hard_delete(self, using=None, keep_parents=False):
        """Permanent delete. Reserved for admin/maintenance only."""
        return super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        """Undo a soft delete."""
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=["deleted_at", "deleted_by", "updated_at"])
