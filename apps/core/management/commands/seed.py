"""Populate the database with realistic sample data for development.

Uses the app factories, so seed data and test data share one source. Refuses to
run when DEBUG is off unless --force is given.
"""

import random

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.billing.tests.factories import BillFactory, BillItemFactory, PaymentFactory
from apps.certificates.tests.factories import CertificateFactory
from apps.core.tests.factories import (
    InstrumentFactory,
    OriginFactory,
    ShapeCutFactory,
    SpeciesFactory,
    StonePriceFactory,
    StoneTypeFactory,
)
from apps.billing.models import Bill
from apps.certificates.models import Certificate
from apps.identification.models import IdentificationReport
from apps.identification.tests.factories import IdentificationReportFactory
from apps.orders.models import Customer, Order
from apps.orders.tests.factories import CustomerFactory, OrderFactory, StoneFactory


class Command(BaseCommand):
    """Seed the database with sample customers, orders, stones, and more."""

    help = "Populate the database with realistic sample data (development only)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--orders", type=int, default=15, help="Number of orders to create."
        )
        parser.add_argument(
            "--force", action="store_true", help="Allow running when DEBUG is off."
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG and not options["force"]:
            raise CommandError("Refusing to seed with DEBUG off. Use --force to override.")

        n_orders = options["orders"]

        # Continue numbering past existing rows so re-runs don't collide on the
        # unique identifier fields. all_objects includes soft-deleted rows.
        CustomerFactory.reset_sequence(Customer.all_objects.count())
        OrderFactory.reset_sequence(Order.all_objects.count())
        IdentificationReportFactory.reset_sequence(IdentificationReport.all_objects.count())
        BillFactory.reset_sequence(Bill.all_objects.count())
        CertificateFactory.reset_sequence(Certificate.all_objects.count())

        # Reference data pools.
        stone_types = [StoneTypeFactory() for _ in range(5)]
        for st in stone_types:
            StonePriceFactory(stone_type=st)
        species = [SpeciesFactory() for _ in range(5)]
        origins = [OriginFactory() for _ in range(4)]
        [ShapeCutFactory() for _ in range(4)]
        [InstrumentFactory() for _ in range(4)]

        reports = billed = certified = 0

        for _ in range(n_orders):
            order = OrderFactory()
            for _ in range(random.randint(1, 4)):
                stone = StoneFactory(
                    order=order, stone_type=random.choice(stone_types)
                )

                # ~70% of stones get an identification report.
                report = None
                if random.random() < 0.7:
                    report = IdentificationReportFactory(
                        stone=stone,
                        species=random.choice(species),
                        origin=random.choice(origins),
                        is_finalized=True,
                    )
                    reports += 1

                # ~40% of reported stones get a certificate.
                if report and random.random() < 0.4:
                    CertificateFactory(stone=stone, report=report)
                    certified += 1

            # ~60% of orders get a bill with a line per stone.
            if random.random() < 0.6:
                bill = BillFactory(order=order)
                for stone in order.stones.all():
                    BillItemFactory(bill=bill, stone=stone)
                if random.random() < 0.5:
                    PaymentFactory(bill=bill)
                billed += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {n_orders} orders — {reports} reports, "
                f"{billed} bills, {certified} certificates."
            )
        )
