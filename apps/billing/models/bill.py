"""Bill (one per order), its line items, and payments."""

from django.db import models
from django.db.models import Q

from apps.core.models import BaseModel

from ..enums import BillStatus
from .provider import ServiceProvider


class Bill(BaseModel):
    """A single bill for an order. Total is the sum of its items."""

    order = models.OneToOneField(
        "orders.Order", on_delete=models.PROTECT, related_name="bill"
    )
    bill_number = models.CharField(max_length=50)
    control_number = models.CharField(max_length=50, blank=True, default="")
    service_provider = models.ForeignKey(
        ServiceProvider, on_delete=models.PROTECT, null=True, blank=True, related_name="bills"
    )
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="TZS")
    status = models.CharField(
        max_length=20, choices=BillStatus.choices, default=BillStatus.PENDING
    )
    issued_at = models.DateTimeField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["bill_number"],
                condition=Q(deleted_at__isnull=True),
                name="unique_active_bill_number",
            ),
            models.UniqueConstraint(
                fields=["control_number"],
                condition=Q(deleted_at__isnull=True) & ~Q(control_number=""),
                name="unique_active_control_number",
            ),
        ]

    def __str__(self) -> str:
        return self.bill_number


class BillItem(BaseModel):
    """A charge line for one stone. Price fields are snapshots at billing time."""

    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name="items")
    stone = models.ForeignKey(
        "orders.Stone", on_delete=models.PROTECT, related_name="bill_items"
    )
    description = models.CharField(max_length=255)
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    weight = models.DecimalField(max_digits=10, decimal_places=3)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    gfs_code = models.CharField(max_length=20, blank=True, default="")
    item_ref = models.CharField(max_length=50, blank=True, default="")

    def __str__(self) -> str:
        return self.description


class Payment(BaseModel):
    """A payment recorded against a bill; supports partial payments."""

    bill = models.ForeignKey(Bill, on_delete=models.PROTECT, related_name="payments")
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    paid_at = models.DateTimeField()
    channel = models.CharField(max_length=50, blank=True, default="")
    reference = models.CharField(max_length=100, blank=True, default="")

    class Meta:
        ordering = ["-paid_at"]

    def __str__(self) -> str:
        return f"{self.amount} on {self.bill}"
