"""Soft-delete queryset and manager.

Records are never physically deleted. ``delete()`` stamps ``deleted_at`` instead.
The default manager hides soft-deleted rows; ``all_objects`` exposes them.
"""

from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    """QuerySet where bulk delete is soft; ``hard_delete`` removes for real."""

    def delete(self):
        """Soft-delete all matched rows in bulk.

        Sets ``deleted_at``. ``deleted_by`` is left for the service layer, since
        a bulk update has no acting user.
        """
        return self.update(deleted_at=timezone.now())

    def hard_delete(self):
        """Permanently delete matched rows. Admin/maintenance only."""
        return super().delete()

    def alive(self):
        """Rows that are not soft-deleted."""
        return self.filter(deleted_at__isnull=True)

    def dead(self):
        """Rows that are soft-deleted."""
        return self.filter(deleted_at__isnull=False)


class SoftDeleteManager(models.Manager):
    """Default manager: returns live (non-deleted) rows only."""

    def get_queryset(self):
        """Base queryset filtered to live rows."""
        return SoftDeleteQuerySet(self.model, using=self._db).alive()
