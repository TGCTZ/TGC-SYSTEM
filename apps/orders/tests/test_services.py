"""Order intake, stone registration, and status transitions."""

from decimal import Decimal

import pytest

from apps.core.enums import StoneStatus
from apps.core.exceptions import ServiceError
from apps.orders.models import StatusHistory
from apps.orders.services import add_stone, create_order, transition_stone
from apps.orders.tests.factories import CustomerFactory

pytestmark = pytest.mark.django_db


def test_create_order_records_count_only(user):
    order = create_order(customer=CustomerFactory(), stone_count=3, user=user)
    assert order.reference_number.startswith("ORD-")
    assert order.stone_count == 3
    assert order.stones.count() == 0  # stones are created later, at identification
    assert order.created_by == user


def test_add_stone_creates_received_stone(user, priced_stone_type):
    order = create_order(customer=CustomerFactory(), stone_count=2, user=user)
    stone = add_stone(
        order, stone_type=priced_stone_type, weight=Decimal("1.5"), user=user
    )
    assert stone.label == "A"
    assert stone.status == StoneStatus.RECEIVED
    assert StatusHistory.objects.filter(
        stone=stone, to_status=StoneStatus.RECEIVED
    ).exists()
    # second stone gets the next label
    stone_b = add_stone(
        order, stone_type=priced_stone_type, weight=Decimal("2.0"), user=user
    )
    assert stone_b.label == "B"


def test_add_stone_beyond_count_raises(user, priced_stone_type):
    order = create_order(customer=CustomerFactory(), stone_count=1, user=user)
    add_stone(order, stone_type=priced_stone_type, weight=Decimal("1"), user=user)
    with pytest.raises(ServiceError):
        add_stone(order, stone_type=priced_stone_type, weight=Decimal("2"), user=user)


def test_transition_records_history(user, priced_stone_type):
    order = create_order(customer=CustomerFactory(), stone_count=1, user=user)
    stone = add_stone(
        order, stone_type=priced_stone_type, weight=Decimal("1"), user=user
    )
    transition_stone(stone, StoneStatus.UNDER_IDENTIFICATION, user=user, note="go")
    stone.refresh_from_db()
    assert stone.status == StoneStatus.UNDER_IDENTIFICATION
    hist = StatusHistory.objects.filter(
        stone=stone, to_status=StoneStatus.UNDER_IDENTIFICATION
    ).first()
    assert hist.from_status == StoneStatus.RECEIVED
    assert hist.changed_by == user


def test_transition_noop_on_same_status(user, priced_stone_type):
    order = create_order(customer=CustomerFactory(), stone_count=1, user=user)
    stone = add_stone(
        order, stone_type=priced_stone_type, weight=Decimal("1"), user=user
    )
    before = StatusHistory.objects.filter(stone=stone).count()
    transition_stone(stone, StoneStatus.RECEIVED, user=user)
    assert StatusHistory.objects.filter(stone=stone).count() == before
