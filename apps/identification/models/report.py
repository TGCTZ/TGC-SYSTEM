"""Identification report (one per stone) and the instruments used on it."""

from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.core.models import BaseModel

from ..enums import Color, OpticCharacter, Transparency, Treatment


class IdentificationReport(BaseModel):
    """A gemmologist's findings for a single stone."""

    stone = models.OneToOneField(
        "orders.Stone", on_delete=models.CASCADE, related_name="report"
    )
    report_number = models.CharField(max_length=50)

    # Reference-table attributes (lookups).
    species = models.ForeignKey(
        "core.Species", on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    variety = models.ForeignKey(
        "core.Variety", on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    origin = models.ForeignKey(
        "core.Origin", on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    shape_cut = models.ForeignKey(
        "core.ShapeCut", on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )

    # Fixed-value attributes (enums).
    color = models.CharField(max_length=20, choices=Color.choices, blank=True, default="")
    transparency = models.CharField(
        max_length=20, choices=Transparency.choices, blank=True, default=""
    )
    treatment = models.CharField(
        max_length=20, choices=Treatment.choices, blank=True, default=""
    )
    optic_character = models.CharField(
        max_length=20, choices=OpticCharacter.choices, blank=True, default=""
    )

    # Measurements.
    refractive_index = models.CharField(max_length=50, blank=True, default="")
    specific_gravity = models.DecimalField(
        max_digits=10, decimal_places=3, null=True, blank=True
    )
    is_polished = models.BooleanField(default=False)
    conclusion = models.TextField(blank=True, default="")

    # Workflow.
    is_finalized = models.BooleanField(default=False)
    identified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    identified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        permissions = [("finalize_report", "Can finalize an identification report")]
        constraints = [
            models.UniqueConstraint(
                fields=["report_number"],
                condition=Q(deleted_at__isnull=True),
                name="unique_active_report_number",
            ),
        ]

    def __str__(self) -> str:
        return self.report_number


class InstrumentUsed(BaseModel):
    """An instrument used during a report, with its reading."""

    report = models.ForeignKey(
        IdentificationReport, on_delete=models.CASCADE, related_name="instruments_used"
    )
    instrument = models.ForeignKey(
        "core.Instrument", on_delete=models.PROTECT, related_name="+"
    )
    reading = models.CharField(max_length=100, blank=True, default="")

    def __str__(self) -> str:
        return f"{self.instrument} ({self.reading})" if self.reading else str(self.instrument)
