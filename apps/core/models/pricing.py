"""Stone pricing: a single fixed price per stone type."""

from django.db import models
from django.db.models import Q

from .base import BaseModel
from .lookups import StoneType


class StonePrice(BaseModel):
    """The fixed amount charged for a stone of a given type (weight-independent)."""

    stone_type = models.OneToOneField(
        StoneType, on_delete=models.PROTECT, related_name="price"
    )
    price = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ["stone_type__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["stone_type"],
                condition=Q(deleted_at__isnull=True),
                name="unique_price_per_stone_type",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.stone_type.name}: {self.price}"
