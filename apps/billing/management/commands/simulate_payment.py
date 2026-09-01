"""Dev-only: simulate a GePG payment so a bill settles."""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.billing.dev import simulate_payment
from apps.billing.models import Bill


class Command(BaseCommand):
    help = "Simulate a GePG payment for a bill (development only)."

    def add_arguments(self, parser):
        parser.add_argument("bill_number", help="e.g. BILL-2026-0004")

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("simulate_payment is only allowed when DEBUG is on.")
        number = options["bill_number"]
        try:
            bill = Bill.objects.get(bill_number=number)
        except Bill.DoesNotExist:
            raise CommandError(f"No bill {number!r}.") from None
        simulate_payment(bill)
        self.stdout.write(
            self.style.SUCCESS(
                f"Settled {bill.bill_number} · status={bill.status} "
                f"· control={bill.control_number}"
            )
        )
