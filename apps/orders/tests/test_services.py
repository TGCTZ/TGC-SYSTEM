"""Order intake and stone status transitions."""

from decimal import Decimal

import pytest

from apps.core.enums import StoneStatus
from apps.orders.models import StatusHistory
from apps.orders.services import create_order, transition_stone
from apps.orders.tests.factories import CustomerFactory

pytestmark = pytest.mark.django_db


def _order(user, stone_type, *weights):
    stones = [{"stone_type": stone_type, "weight": Decimal(w)} for w in weights]
    return create_order(customer=CustomerFactory(), stones=stones, user=user)


def test_create_order_creates_stones_and_history(user, priced_stone_type):
    order = _order(user, priced_stone_type, "1.5", "2.0")
    assert order.reference_no.startswith("ORD-")
    assert order.stones.count() == 2
    stone = order.stones.first()
    assert stone.status == StoneStatus.RECEIVED
    assert stone.created_by == user
    assert StatusHistory.objects.filter(
        stone=stone, to_status=StoneStatus.RECEIVED
    ).exists()


def test_transition_records_history(user, priced_stone_type):
    order = _order(user, priced_stone_type, "1.0")
    stone = order.stones.first()
    transition_stone(stone, StoneStatus.UNDER_IDENTIFICATION, user=user, note="go")
    stone.refresh_from_db()
    assert stone.status == StoneStatus.UNDER_IDENTIFICATION
    hist = StatusHistory.objects.filter(
        stone=stone, to_status=StoneStatus.UNDER_IDENTIFICATION
    ).first()
    assert hist.from_status == StoneStatus.RECEIVED
    assert hist.changed_by == user


def test_transition_noop_on_same_status(user, priced_stone_type):
    order = _order(user, priced_stone_type, "1.0")
    stone = order.stones.first()
    before = StatusHistory.objects.filter(stone=stone).count()
    transition_stone(stone, StoneStatus.RECEIVED, user=user)
    assert StatusHistory.objects.filter(stone=stone).count() == before
