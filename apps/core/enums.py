"""Enums shared across modules. App-specific enums live with their app."""

from django.db import models


class StoneStatus(models.TextChoices):
    """Per-stone lifecycle stages. Allowed transitions are enforced in services."""

    RECEIVED = ("received", "Received")
    UNDER_IDENTIFICATION = ("under_identification", "Under identification")
    BILLED = ("billed", "Billed")
    PAID = ("paid", "Paid")
    CERTIFIED = ("certified", "Certified")
    READY_FOR_COLLECTION = ("ready_for_collection", "Ready for collection")
    COLLECTED = ("collected", "Collected")
    ON_HOLD = ("on_hold", "On hold")
    CANCELLED = ("cancelled", "Cancelled")


class StoneCategory(models.TextChoices):
    """Stone classification; drives pricing tiers."""

    PRECIOUS = ("precious", "Precious")
    SEMI_PRECIOUS = ("semi_precious", "Semi-precious")
    DIAMOND = ("diamond", "Diamond")


class WeightUnit(models.TextChoices):
    """Unit for stone weight and pricing."""

    CARAT = ("carat", "Carat")
    GRAM = ("gram", "Gram")

    @property
    def symbol(self) -> str:
        """Short display symbol, e.g. 'ct' or 'g'."""
        return {self.CARAT: "ct", self.GRAM: "g"}[self]
