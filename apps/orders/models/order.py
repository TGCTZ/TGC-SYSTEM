"""Order grouping the stones a customer submits in one visit."""

from django.db import models
from django.db.models import Q

from apps.core.models import BaseModel

from .customer import Customer


class Order(BaseModel):
    """A batch of stones received from a customer. Status lives on each stone."""

    reference_no = models.CharField(max_length=30)
    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name="orders"
    )
    received_date = models.DateField()
    stone_count = models.PositiveIntegerField(
        default=0, help_text="Number of stones the customer submitted."
    )

    class Meta:
        ordering = ["-received_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["reference_no"],
                condition=Q(deleted_at__isnull=True),
                name="unique_active_order_reference_no",
            ),
        ]

    @property
    def identified_count(self) -> int:
        """Number of stones created (identified) so far."""
        return self.stones.count()

    def __str__(self) -> str:
        return self.reference_no
