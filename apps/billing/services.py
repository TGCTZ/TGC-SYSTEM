"""Billing services: GePG bill submission and payment-notification handling.

Payment is control-number based and confirmed asynchronously by GePG — there is
no manual payment entry. ``generate_bill_for_order`` submits a bill and obtains a
control number; ``process_payment_notification`` handles the GePG callback.
"""

import logging
import xml.etree.ElementTree as ET
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.core.enums import StoneStatus
from apps.core.exceptions import ServiceError
from apps.core.models import StonePrice
from apps.core.services import generate_reference_number
from apps.orders.services import transition_stone

from .enums import BillStatus
from .gateways.gepg import (
    build_bill_response_ack,
    build_payment_ack,
    parse_bill_response,
    parse_payment_notification,
    submit_bill,
)
from .models import Bill, BillItem, Payment

logger = logging.getLogger(__name__)


def _price_for(stone) -> Decimal:
    """Active unit price for a stone's type, or raise if none is set."""
    price = StonePrice.objects.filter(stone_type=stone.stone_type, is_active=True).first()
    if price is None:
        raise ServiceError(f"No active price for stone type '{stone.stone_type}'.")
    return price.price_per_unit


@transaction.atomic
def _create_local_bill(order, service_provider, user) -> Bill:
    """Create the bill and its snapshotted line items; mark stones billed."""
    if Bill.objects.filter(order=order).exists():
        raise ServiceError(f"Order {order.reference_no} already has a bill.")
    stones = list(order.stones.all())
    if not stones:
        raise ServiceError("Order has no stones to bill.")

    now = timezone.now()
    bill = Bill(
        order=order,
        bill_number=generate_reference_number(Bill, "bill_number", "BILL"),
        service_provider=service_provider,
        status=BillStatus.PENDING,
        issued_at=now,
        expiry_at=now + timedelta(days=settings.GEPG_BILL_EXPIRY_DAYS),
    )
    if user is not None:
        bill.created_by = user
    bill.save()

    total = Decimal("0")
    for stone in stones:
        unit_price = _price_for(stone)
        amount = (unit_price * stone.weight).quantize(Decimal("0.01"))
        item = BillItem(
            bill=bill,
            stone=stone,
            description=f"{stone.stone_type.name} — {stone.weight} {stone.weight_unit}",
            unit_price=unit_price,
            weight=stone.weight,
            amount=amount,
            gfs_code=settings.GEPG_GFS_CODE,
            item_ref=f"B{bill.id}IT-{stone.id}",
        )
        if user is not None:
            item.created_by = user
        item.save()
        total += amount
        transition_stone(stone, StoneStatus.BILLED, user=user, note=f"Billed on {bill.bill_number}")

    bill.total_amount = total
    bill.save(update_fields=["total_amount", "updated_at"])
    return bill


def generate_bill_for_order(order, *, service_provider=None, user=None) -> Bill:
    """Create a bill for an order and submit it to GePG for a control number.

    The local bill is committed first; the GePG call happens outside that
    transaction and updates the bill with the control number / status.
    """
    bill = _create_local_bill(order, service_provider, user)

    username = user.get_username() if user is not None else "System"
    result = submit_bill(bill, order.customer, username)

    bill.gepg_submitted = True
    bill.gepg_submitted_at = timezone.now()
    bill.status_code = result["status_code"] or ""
    bill.status_desc = result["status_desc"] or ""
    if result["success"] and result["control_number"] not in (None, "PENDING"):
        bill.control_number = result["control_number"]
    bill.save(
        update_fields=[
            "gepg_submitted", "gepg_submitted_at", "status_code", "status_desc",
            "control_number", "updated_at",
        ]
    )
    return bill


def process_payment_notification(xml_content: str) -> str:
    """Handle a GePG payment notification callback; return a signed ack XML."""
    try:
        header, transactions = parse_payment_notification(xml_content)
    except (ValueError, ET.ParseError) as exc:
        logger.error("Invalid GePG payment notification: %s", exc)
        return build_payment_ack("ERROR", "7102")

    req_id = header["req_id"]
    try:
        for txn in transactions:
            _apply_payment(header, txn, xml_content)
    except Exception:
        logger.exception("Failed to process GePG payment notification")
        return build_payment_ack(req_id or "ERROR", "7102")
    return build_payment_ack(req_id, "7101")


@transaction.atomic
def _apply_payment(header: dict, txn: dict, raw: str) -> None:
    """Record one payment transaction and settle its bill if fully paid."""
    bill = (
        Bill.objects.filter(bill_number=txn["gepg_bill_id"]).first()
        or Bill.objects.filter(control_number=txn["bill_ctr_num"]).first()
    )
    if bill is None:
        raise ServiceError(f"Bill '{txn['gepg_bill_id']}' not found.")

    defaults = {**header, **txn, "bill": bill, "processed": True, "raw_request": raw}
    defaults.pop("trx_id", None)
    payment, created = Payment.objects.get_or_create(
        trx_id=txn["trx_id"], defaults=defaults
    )
    if not created:
        for field, value in defaults.items():
            setattr(payment, field, value)
        payment.save()
        return

    paid = sum((p.paid_amount or Decimal("0") for p in bill.payments.all()), Decimal("0"))
    if paid >= bill.total_amount:
        bill.status = BillStatus.PAID
        for stone in bill.order.stones.all():
            transition_stone(stone, StoneStatus.PAID, note="Bill settled via GePG")
    else:
        bill.status = BillStatus.PARTIALLY_PAID
    bill.save(update_fields=["status", "updated_at"])


@transaction.atomic
def handle_bill_response_callback(xml_content: str) -> str:
    """Handle an async billSubRes callback: store the control number; return ack."""
    try:
        data = parse_bill_response(xml_content)
    except (ValueError, ET.ParseError) as exc:
        logger.error("Invalid GePG bill response: %s", exc)
        return build_bill_response_ack("ERROR", "7102")

    bill = Bill.objects.filter(bill_number=data["bill_id"]).first()
    if bill is not None and data["control_number"]:
        bill.control_number = data["control_number"]
        bill.status_code = data["status_code"]
        bill.status_desc = data["status_desc"]
        bill.save(update_fields=["control_number", "status_code", "status_desc", "updated_at"])
    return build_bill_response_ack(data["res_id"], "7101")
