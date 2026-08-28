"""Factories for billing."""

import factory
from django.utils import timezone
from factory.fuzzy import FuzzyDecimal

from apps.billing.models import Bill, BillItem, Payment, ServiceProvider
from apps.orders.tests.factories import OrderFactory, StoneFactory


class ServiceProviderFactory(factory.django.DjangoModelFactory):
    """Builds a GePG service provider."""

    class Meta:
        model = ServiceProvider

    sp_code = factory.Sequence(lambda n: f"SP{n:04d}")
    name = factory.Faker("company")


class BillFactory(factory.django.DjangoModelFactory):
    """Builds a bill for a new order."""

    class Meta:
        model = Bill

    order = factory.SubFactory(OrderFactory)
    bill_number = factory.Sequence(lambda n: f"BILL-{n:05d}")
    total_amount = FuzzyDecimal(100_000, 10_000_000)


class BillItemFactory(factory.django.DjangoModelFactory):
    """Builds a bill line item with snapshot prices."""

    class Meta:
        model = BillItem

    bill = factory.SubFactory(BillFactory)
    stone = factory.SubFactory(StoneFactory)
    description = factory.Faker("sentence", nb_words=4)
    unit_price = FuzzyDecimal(50_000, 1_000_000)
    weight = FuzzyDecimal(0.5, 50, precision=3)
    amount = FuzzyDecimal(100_000, 5_000_000)


class PaymentFactory(factory.django.DjangoModelFactory):
    """Builds a payment against a new bill."""

    class Meta:
        model = Payment

    bill = factory.SubFactory(BillFactory)
    amount = FuzzyDecimal(100_000, 5_000_000)
    paid_at = factory.LazyFunction(timezone.now)
    channel = "gepg"
