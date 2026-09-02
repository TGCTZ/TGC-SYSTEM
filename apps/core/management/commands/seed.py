"""Populate the database with realistic sample data for development.

Uses the app factories, so seed data and test data share one source. Refuses to
run when DEBUG is off unless --force is given.
"""

import random
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.billing.enums import BillStatus
from apps.billing.models import Bill, Payment
from apps.billing.tests.factories import BillFactory, BillItemFactory, PaymentFactory
from apps.certificates.models import Certificate
from apps.certificates.tests.factories import CertificateFactory
from apps.core.enums import ColorGroup, StoneCategory, StoneStatus
from apps.core.tests.factories import (
    ColorFactory,
    InstrumentFactory,
    OriginFactory,
    ShapeCutFactory,
    SpeciesFactory,
    StonePriceFactory,
    StoneTypeFactory,
    VarietyFactory,
)
from apps.identification.enums import NatureType
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
            raise CommandError(
                "Refusing to seed with DEBUG off. Use --force to override."
            )

        n_orders = options["orders"]

        # Continue numbering past existing rows so re-runs don't collide on the
        # unique identifier fields. all_objects includes soft-deleted rows.
        CustomerFactory.reset_sequence(Customer.all_objects.count())
        OrderFactory.reset_sequence(Order.all_objects.count())
        IdentificationReportFactory.reset_sequence(
            IdentificationReport.all_objects.count()
        )
        BillFactory.reset_sequence(Bill.all_objects.count())
        PaymentFactory.reset_sequence(Payment.all_objects.count())
        CertificateFactory.reset_sequence(Certificate.all_objects.count())

        # The three fixed-price stone types.
        type_specs = [
            ("Precious", StoneCategory.PRECIOUS, Decimal("30000")),
            ("Semi-precious", StoneCategory.SEMI_PRECIOUS, Decimal("10000")),
            ("Diamond", StoneCategory.DIAMOND, Decimal("40000")),
        ]
        stone_types, price_of = [], {}
        for name, category, price in type_specs:
            st = StoneTypeFactory(name=name, category=category)
            StonePriceFactory(stone_type=st, price=price)
            stone_types.append(st)
            price_of[st.pk] = price

        # Real gemmological reference data — editable later at /backoffice/.
        for name in (
            "Color filter",
            "Diamond tester",
            "Dichroscope",
            "Hardness pencil",
            "Hydrostatic scale",
            "Microscope",
            "Polariscope",
            "Refractometer",
            "Spectroscope",
            "UV fluorescence",
        ):
            InstrumentFactory(name=name)

        origins = [
            OriginFactory(name=name)
            for name in (
                "Tanzania",
                "Sri Lanka",
                "Myanmar",
                "Mozambique",
                "Madagascar",
                "Zambia",
                "Kenya",
                "Thailand",
                "Brazil",
                "Colombia",
            )
        ]
        shapes = [
            ShapeCutFactory(name=name)
            for name in (
                "Round",
                "Oval",
                "Cushion",
                "Emerald cut",
                "Pear",
                "Marquise",
                "Princess",
                "Heart",
                "Trillion",
                "Cabochon",
            )
        ]

        # Species with their varieties (variety.species keeps the pair consistent).
        species_specs = {
            "Corundum": ["Ruby", "Sapphire"],
            "Beryl": ["Emerald", "Aquamarine"],
            "Tourmaline": ["Rubellite"],
            "Quartz": ["Amethyst", "Citrine"],
            "Garnet": [],
            "Spinel": [],
            "Chrysoberyl": [],
            "Zircon": [],
            "Topaz": [],
            "Peridot": [],
        }
        varieties = []
        for sp_name, var_names in species_specs.items():
            sp = SpeciesFactory(name=sp_name)
            varieties += [VarietyFactory(name=v, species=sp) for v in var_names]

        # GIA-style color families, matching the legacy finding form.
        color_specs = {
            ColorGroup.WHITE_GREY_BLACK: ["Colourless", "White", "Grey", "Black"],
            ColorGroup.PURPLE_VIOLET: [
                "Purple",
                "Reddish Purple",
                "Red-Purple",
                "Violetish Purple",
                "Bluish Violet",
                "Violet",
            ],
            ColorGroup.RED_PINK: [
                "Strongly Purplish Red",
                "Slightly Purplish Red",
                "Red",
                "Orangy Red",
                "Red-Orange",
                "Pink",
                "Brown",
            ],
            ColorGroup.ORANGE_YELLOW: [
                "Reddish Orange",
                "Orange",
                "Yellowish Orange",
                "Orangy Yellow",
                "Yellow",
                "Greenish Yellow",
            ],
            ColorGroup.GREEN: [
                "Yellow-Green",
                "Strongly Yellowish Green",
                "Yellowish Green",
                "Slightly Yellowish Green",
                "Green",
                "Very Slightly Bluish Green",
                "Bluish Green",
                "Very Strongly Bluish Green",
                "Green-Blue",
            ],
            ColorGroup.BLUE: [
                "Very Strongly Greenish Blue",
                "Greenish Blue",
                "Very Slightly Greenish Blue",
                "Blue",
                "Violetish Blue",
            ],
        }
        colors = [
            ColorFactory(name=name, group=group)
            for group, names in color_specs.items()
            for name in names
        ]

        buckets = {"typing": 0, "billable": 0, "findings": 0, "done": 0}

        for i in range(n_orders):
            n = random.randint(1, 3)
            order = OrderFactory(stone_count=n)
            phase = i % 4  # spread orders across the pipeline

            if phase == 0:  # partially registered → type-identification worklist
                for _ in range(random.randint(0, n - 1)):
                    StoneFactory(
                        order=order, stone_type=random.choice(stone_types), weight=None
                    )
                buckets["typing"] += 1
                continue

            stones = [
                StoneFactory(
                    order=order, stone_type=random.choice(stone_types), weight=None
                )
                for _ in range(n)
            ]

            if phase == 1:  # fully registered, unbilled → billing worklist
                buckets["billable"] += 1
                continue

            # Billed and paid.
            total = sum((price_of[s.stone_type_id] for s in stones), Decimal("0"))
            bill = BillFactory(order=order, status=BillStatus.PAID, total_amount=total)
            # Base the control number on the unique pk so re-runs never collide.
            bill.control_number = f"9944{bill.pk:08d}"
            bill.save(update_fields=["control_number"])
            for s in stones:
                amount = price_of[s.stone_type_id]
                BillItemFactory(
                    bill=bill,
                    stone=s,
                    description=s.stone_type.name,
                    unit_price=amount,
                    amount=amount,
                )
                s.status = StoneStatus.PAID
                s.save(update_fields=["status"])
            PaymentFactory(bill=bill, paid_amount=total)

            if phase == 2:  # paid, awaiting findings → findings worklist
                buckets["findings"] += 1
                continue

            # Phase 3: findings recorded and finalized (+ some certificates).
            for s in stones:
                s.weight = Decimal(str(round(random.uniform(0.5, 12), 3)))
                s.save(update_fields=["weight"])
                variety = random.choice(varieties)
                report = IdentificationReportFactory(
                    stone=s,
                    species=variety.species,
                    variety=variety,
                    color=random.choice(colors),
                    nature_type=NatureType.NATURAL,
                    origin=random.choice(origins),
                    shape_cut=random.choice(shapes),
                    dimensions=(
                        f"{round(random.uniform(4, 9), 1)} x "
                        f"{round(random.uniform(3, 7), 1)} x "
                        f"{round(random.uniform(2, 5), 1)} mm"
                    ),
                    is_finalized=True,
                )
                if random.random() < 0.6:
                    CertificateFactory(stone=s, report=report)
                    s.status = StoneStatus.CERTIFIED
                    s.save(update_fields=["status"])
            buckets["done"] += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {n_orders} orders — {buckets['typing']} typing, "
                f"{buckets['billable']} billable, {buckets['findings']} awaiting "
                f"findings, {buckets['done']} completed."
            )
        )
