"""Stone pricing: rate per stone type."""

from django.db import models
from django.db.models import Q

from apps.core.enums import WeightUnit

from .base import BaseModel
from .lookups import StoneType


class StonePrice(BaseModel):
    """Active price per stone type, charged per weight unit."""

    stone_type = models.ForeignKey(
        StoneType, on_delete=models.PROTECT, related_name="prices"
    )
    price_per_unit = models.DecimalField(max_digits=15, decimal_places=2)
    unit = models.CharField(max_length=10, choices=WeightUnit.choices)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["stone_type__name"]
        constraints = [
            # One active price per stone type, among live rows.
            models.UniqueConstraint(
                fields=["stone_type"],
                condition=Q(deleted_at__isnull=True, is_active=True),
                name="unique_active_price_per_stone_type",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.stone_type.name}: {self.price_per_unit} / {self.unit}"
