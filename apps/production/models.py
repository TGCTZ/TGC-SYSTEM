"""Production step performed on a stone."""

from django.conf import settings
from django.db import models

from apps.core.models import BaseModel

from .enums import ProductionType, QAResult


class Production(BaseModel):
    """One workshop step (sonara/carving/lapidary) on a stone."""

    stone = models.ForeignKey(
        "orders.Stone", on_delete=models.CASCADE, related_name="productions"
    )
    type = models.CharField(max_length=20, choices=ProductionType.choices)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    qa_result = models.CharField(
        max_length=20, choices=QAResult.choices, default=QAResult.PENDING
    )
    qa_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["stone", "started_at"]

    def __str__(self) -> str:
        return f"{self.get_type_display()} — {self.stone}"
