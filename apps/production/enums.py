"""Enums owned by production."""

from django.db import models


class ProductionType(models.TextChoices):
    """The workshop performing the work."""

    SONARA = ("sonara", "Sonara")
    CARVING = ("carving", "Carving")
    LAPIDARY = ("lapidary", "Lapidary")


class QAResult(models.TextChoices):
    """Quality-assurance outcome for a production step."""

    PENDING = ("pending", "Pending")
    PASSED = ("passed", "Passed")
    FAILED = ("failed", "Failed")
