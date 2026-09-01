"""Partial-unique constraints on reference data and pricing."""

import pytest

from django.db import IntegrityError, transaction

from apps.core.models import StonePrice, StoneType
from apps.core.tests.factories import StonePriceFactory, StoneTypeFactory

pytestmark = pytest.mark.django_db


def test_reference_name_unique_among_live():
    StoneTypeFactory(name="Ruby")
    with transaction.atomic(), pytest.raises(IntegrityError):
        StoneType.objects.create(name="Ruby", category="precious")


def test_reference_name_reusable_after_soft_delete():
    st = StoneTypeFactory(name="Ruby")
    st.delete()
    st2 = StoneType.objects.create(name="Ruby", category="precious")
    assert st2.pk


def test_one_price_per_stone_type():
    st = StoneTypeFactory()
    StonePriceFactory(stone_type=st)
    with transaction.atomic(), pytest.raises(IntegrityError):
        StonePrice.objects.create(stone_type=st, price=1000)
