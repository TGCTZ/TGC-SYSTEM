"""Order intake and stone status transitions."""

from django.db import transaction
from django.utils import timezone

from apps.core.enums import StoneStatus, WeightUnit
from apps.core.exceptions import ServiceError
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


def create_order(*, customer, stone_count: int, received_date=None, user=None) -> Order:
    """Register an order and how many stones the customer submitted.

    Reception records only the count; the individual stones (with their
    properties) are created later during identification via :func:`add_stone`.
    """
    order = Order(
        reference_no=generate_reference_number(Order, "reference_no", "ORD"),
        customer=customer,
        received_date=received_date or timezone.now().date(),
        stone_count=stone_count,
    )
    if user is not None:
        order.created_by = user
    order.save()
    return order


@transaction.atomic
def add_stone(order: Order, *, stone_type, weight, weight_unit=WeightUnit.CARAT,
              user=None) -> Stone:
    """Add a stone to an order (created during identification) as ``received``.

    The label is the next letter in the order (A, B, C…). Refuses to register more
    stones than the customer submitted (``order.stone_count``).
    """
    registered = order.stones.count()
    if registered >= order.stone_count:
        raise ServiceError(
            f"All {order.stone_count} stone(s) for {order.reference_no} are "
            f"already registered."
        )
    label = chr(65 + registered)
    stone = Stone(
        order=order,
        label=label,
        stone_type=stone_type,
        weight=weight,
        weight_unit=weight_unit,
        status=StoneStatus.RECEIVED,
    )
    if user is not None:
        stone.created_by = user
    stone.save()
    StatusHistory.objects.create(
        stone=stone, to_status=StoneStatus.RECEIVED, changed_by=user, note="Registered"
    )
    return stone


def update_stone(stone: Stone, *, stone_type=None, weight=None, weight_unit=None,
                 user=None) -> Stone:
    """Update a stone's recorded properties (during identification)."""
    if stone_type is not None:
        stone.stone_type = stone_type
    if weight is not None:
        stone.weight = weight
    if weight_unit:
        stone.weight_unit = weight_unit
    if user is not None:
        stone.updated_by = user
    stone.save(update_fields=["stone_type", "weight", "weight_unit", "updated_at", "updated_by"])
    return stone
