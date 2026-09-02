"""Per-year reference number generation."""

import pytest
from django.utils import timezone

from apps.core.services import generate_reference_number
from apps.orders.models import Order
from apps.orders.tests.factories import OrderFactory

pytestmark = pytest.mark.django_db


def test_first_number_of_year():
    year = timezone.now().year
    assert generate_reference_number(Order, "reference_number", "ORD") == f"ORD-{year}-0001"


def test_increments_from_existing():
    year = timezone.now().year
    OrderFactory(reference_number=f"ORD-{year}-0005")
    assert generate_reference_number(Order, "reference_number", "ORD") == f"ORD-{year}-0006"


def test_includes_soft_deleted():
    year = timezone.now().year
    order = OrderFactory(reference_number=f"ORD-{year}-0009")
    order.delete()
    assert generate_reference_number(Order, "reference_number", "ORD") == f"ORD-{year}-0010"
