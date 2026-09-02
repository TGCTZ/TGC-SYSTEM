"""Factories for billing."""

import factory
from factory.fuzzy import FuzzyDecimal

from django.utils import timezone

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
    unit_price = FuzzyDecimal(10_000, 40_000)
    amount = FuzzyDecimal(10_000, 40_000)


class PaymentFactory(factory.django.DjangoModelFactory):
    """Builds a GePG payment notification against a new bill."""

    class Meta:
        model = Payment

    bill = factory.SubFactory(BillFactory)
    gepg_bill_id = factory.LazyAttribute(lambda o: o.bill.bill_number)
    trx_id = factory.Sequence(lambda n: f"TRX{n:08d}")
    pay_ref_id = factory.Sequence(lambda n: f"REF{n:08d}")
    psp_name = "M-Pesa"
    paid_amount = FuzzyDecimal(100_000, 5_000_000)
    currency = "TZS"
    trx_dt_tm = factory.LazyFunction(timezone.now)
    is_processed = True
