"""Shared service helpers for the core layer."""

from django.db import models
from django.utils import timezone


def generate_reference_number(
    model: type[models.Model], field: str, prefix: str
) -> str:
    """Return the next per-year reference like ``PREFIX-2026-0001``.

    Scans existing values (including soft-deleted, so numbers are never reused)
    for the current year and increments the highest. Call inside the creating
    transaction; the field's unique constraint is the backstop against races.
    """
    year = timezone.now().year
    stem = f"{prefix}-{year}-"
    manager = getattr(model, "all_objects", model._default_manager)
    last = (
        manager.filter(**{f"{field}__startswith": stem})
        .order_by(f"-{field}")
        .values_list(field, flat=True)
        .first()
    )
    next_seq = int(last.rsplit("-", 1)[1]) + 1 if last else 1
    return f"{stem}{next_seq:04d}"
