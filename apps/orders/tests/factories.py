"""Factories for orders."""

import factory
from factory.fuzzy import FuzzyChoice, FuzzyDecimal

from apps.core.enums import StoneStatus, WeightUnit
from apps.core.tests.factories import StoneTypeFactory
from apps.orders.models import Customer, Order, StatusHistory, Stone


class CustomerFactory(factory.django.DjangoModelFactory):
    """Builds a customer."""

    class Meta:
        model = Customer

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    phone = factory.Sequence(lambda n: f"07{n:08d}")
    email = factory.Faker("email")
    region = factory.Faker("city")


class OrderFactory(factory.django.DjangoModelFactory):
    """Builds an order for a new customer."""

    class Meta:
        model = Order

    reference_no = factory.Sequence(lambda n: f"ORD-{n:05d}")
    customer = factory.SubFactory(CustomerFactory)
    received_date = factory.Faker("date_this_year")


class StoneFactory(factory.django.DjangoModelFactory):
    """Builds a stone in a new order."""

    class Meta:
        model = Stone

    order = factory.SubFactory(OrderFactory)
    label = factory.Sequence(lambda n: chr(65 + n % 26))
    stone_type = factory.SubFactory(StoneTypeFactory)
    weight = FuzzyDecimal(0.5, 50, precision=3)
    weight_unit = WeightUnit.CARAT
    quantity = 1
    status = StoneStatus.RECEIVED


class StatusHistoryFactory(factory.django.DjangoModelFactory):
    """Builds a status-transition record for a stone."""

    class Meta:
        model = StatusHistory

    stone = factory.SubFactory(StoneFactory)
    to_status = FuzzyChoice(StoneStatus.values)
