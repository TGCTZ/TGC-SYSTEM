"""Order intake and stone status transitions."""

from django.db import transaction
from django.utils import timezone

from apps.core.enums import StoneStatus, WeightUnit
from apps.core.services import generate_reference_number

from .models import Order, StatusHistory, Stone


def transition_stone(stone: Stone, to_status: str, *, user=None, note: str = "") -> Stone:
    """Move a stone to a new status and record it in the audit trail.

    No-ops if the stone is already in ``to_status``. Transition rules (B5/B6) are
    assumed permissive for now.
    """
    if stone.status == to_status:
        return stone
    from_status = stone.status
    stone.status = to_status
    if user is not None:
        stone.updated_by = user
    stone.save(update_fields=["status", "updated_at", "updated_by"])
    StatusHistory.objects.create(
        stone=stone,
        from_status=from_status,
        to_status=to_status,
        changed_by=user,
        note=note,
    )
    return stone


@transaction.atomic
def create_order(*, customer, stones: list[dict], received_date=None, user=None) -> Order:
    """Create an order with its stones, each logged as ``received``.

    ``stones`` is a list of dicts with ``stone_type`` and ``weight`` (and
    optional ``weight_unit``, ``quantity``, ``label``).
    """
    order = Order(
        reference_no=generate_reference_number(Order, "reference_no", "ORD"),
        customer=customer,
        received_date=received_date or timezone.now().date(),
    )
    if user is not None:
        order.created_by = user
    order.save()

    for index, data in enumerate(stones):
        stone = Stone(
            order=order,
            label=data.get("label") or chr(65 + index),
            stone_type=data["stone_type"],
            weight=data["weight"],
            weight_unit=data.get("weight_unit", WeightUnit.CARAT),
            quantity=data.get("quantity", 1),
            status=StoneStatus.RECEIVED,
        )
        if user is not None:
            stone.created_by = user
        stone.save()
        StatusHistory.objects.create(
            stone=stone, to_status=StoneStatus.RECEIVED, changed_by=user,
            note="Order received",
        )
    return order
