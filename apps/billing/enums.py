"""Enums owned by billing."""

from django.db import models


class BillStatus(models.TextChoices):
    """Payment state of a bill."""

    PENDING = ("pending", "Pending")
    PARTIALLY_PAID = ("partially_paid", "Partially paid")
    PAID = ("paid", "Paid")
    CANCELLED = ("cancelled", "Cancelled")
    EXPIRED = ("expired", "Expired")
