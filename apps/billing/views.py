"""Billing views: staff bill management (list, worklist, generate, detail) and the
GePG inbound webhook endpoints (called by GePG, CSRF-exempt)."""

import logging
import xml.etree.ElementTree as ET

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Count, F, Q, Sum
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import ListView

from apps.core.exceptions import ServiceError
from apps.core.row_actions import action
from apps.orders.models import Order

from .dev import simulate_payment as simulate_gepg_payment
from .enums import BillStatus
from .models import Bill, Payment
from .services import (
    generate_bill_for_order,
    handle_bill_response_callback,
    process_payment_notification,
)

logger = logging.getLogger(__name__)

# Bill status -> badge variant for the UI.
_STATUS_VARIANT = {
    BillStatus.PENDING: "warning",
    BillStatus.PARTIALLY_PAID: "info",
    BillStatus.PAID: "success",
    BillStatus.CANCELLED: "danger",
    BillStatus.EXPIRED: "danger",
}


# --- staff-facing bill management ------------------------------------------
class BillListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Searchable, filterable, paginated list of bills."""

    permission_required = "billing.view_bill"
    template_name = "pages/billing/index.html"
    context_object_name = "bills"
    paginate_by = 5

    def get_queryset(self):
        qs = Bill.objects.select_related("order__customer").order_by("-created_at")
        query = self.request.GET.get("q", "").strip()
        if query:
            qs = qs.filter(
                Q(bill_number__icontains=query)
                | Q(control_number__icontains=query)
                | Q(status__icontains=query)
                | Q(order__reference_number__icontains=query)
                | Q(order__customer__first_name__icontains=query)
                | Q(order__customer__last_name__icontains=query)
                | Q(order__customer__company_name__icontains=query)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["can_generate"] = self.request.user.has_perm("billing.generate_bill")
        for bill in ctx["bills"]:
            bill.status_variant = _STATUS_VARIANT.get(bill.status, "warning")
            bill.row_actions = [
                action("View", "lucide:eye", reverse("billing:detail", args=[bill.pk]))
            ]
        return ctx


class BillingWorklistView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Orders fully identified (every stone's report finalized) and not yet billed."""

    permission_required = "billing.generate_bill"
    template_name = "pages/billing/worklist.html"
    context_object_name = "orders"
    paginate_by = 5

    def get_queryset(self):
        # Billable once every stone is registered and typed (price known);
        # findings are recorded after payment.
        qs = (
            Order.objects.select_related("customer")
            .annotate(registered=Count("stones"))
            .filter(bill__isnull=True, stone_count__gt=0, registered=F("stone_count"))
            .order_by("received_date")
        )
        query = self.request.GET.get("q", "").strip()
        if query:
            qs = qs.filter(
                Q(reference_number__icontains=query)
                | Q(customer__first_name__icontains=query)
                | Q(customer__last_name__icontains=query)
                | Q(customer__company_name__icontains=query)
            )
        return qs


@login_required
@permission_required("billing.generate_bill", raise_exception=True)
@require_POST
def bill_generate(request, order_pk):
    """Create a bill for an order and submit it to GePG for a control number."""
    order = get_object_or_404(Order, pk=order_pk)
    try:
        bill = generate_bill_for_order(order, user=request.user)
    except ServiceError as exc:
        messages.error(request, str(exc))
        return redirect("billing:worklist")
    if bill.control_number:
        messages.success(
            request,
            f"Bill {bill.bill_number} created · control number {bill.control_number}.",
        )
    else:
        messages.warning(
            request,
            f"Bill {bill.bill_number} created. Awaiting a GePG control number.",
        )
    return redirect("billing:detail", pk=bill.pk)


@login_required
@permission_required("billing.view_bill", raise_exception=True)
def bill_detail(request, pk):
    """Bill detail: line items, GePG status, and payments received."""
    bill = get_object_or_404(
        Bill.objects.select_related("order__customer", "service_provider"), pk=pk
    )
    payments = (
        bill.payments.all() if request.user.has_perm("billing.view_payment") else None
    )
    return render(
        request,
        "pages/billing/detail.html",
        {
            "bill": bill,
            "items": bill.items.select_related("stone__stone_type").all(),
            "payments": payments,
            "status_variant": _STATUS_VARIANT.get(bill.status, "warning"),
            "can_simulate": settings.DEBUG and bill.status != BillStatus.PAID,
        },
    )


@login_required
@permission_required("billing.generate_bill", raise_exception=True)
@require_POST
def payment_simulate(request, pk):
    """Dev-only: settle a bill via a simulated GePG payment. Absent in production."""
    if not settings.DEBUG:
        raise Http404
    bill = get_object_or_404(Bill, pk=pk)
    simulate_gepg_payment(bill)
    messages.success(
        request, f"Simulated payment for {bill.bill_number} — bill settled."
    )
    return redirect("billing:detail", pk=bill.pk)


class PaymentListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Global payments feed across all bills, for reconciliation."""

    permission_required = "billing.view_payment"
    template_name = "pages/billing/payments.html"
    context_object_name = "payments"
    paginate_by = 5

    def get_queryset(self):
        qs = Payment.objects.select_related("bill").order_by("-trx_dt_tm")
        query = self.request.GET.get("q", "").strip()
        if query:
            qs = qs.filter(
                Q(trx_id__icontains=query)
                | Q(pyr_name__icontains=query)
                | Q(psp_name__icontains=query)
                | Q(bill__bill_number__icontains=query)
                | Q(bill__control_number__icontains=query)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["query"] = self.request.GET.get("q", "")
        # Totals over the full filtered result (not just this page).
        totals = self.object_list.aggregate(total=Sum("paid_amount"), count=Count("id"))
        ctx["total_paid"] = totals["total"] or 0
        ctx["payment_count"] = totals["count"]
        return ctx


def _pretty_xml(raw: str) -> str:
    """Indent stored GePG XML for display; return it unchanged if it won't parse."""
    try:
        root = ET.fromstring(raw)  # noqa: S314 — our own stored payload, display only
    except ET.ParseError:
        return raw
    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="unicode")


@login_required
@permission_required("billing.view_payment", raise_exception=True)
def payment_detail(request, pk):
    """Full detail for one payment — every field GePG sent, plus the raw payload."""
    payment = get_object_or_404(
        Payment.objects.select_related("bill__order__customer"), pk=pk
    )
    return render(
        request,
        "pages/billing/payment_detail.html",
        {
            "payment": payment,
            "raw_pretty": _pretty_xml(payment.raw_request)
            if payment.raw_request
            else "",
        },
    )


# --- GePG inbound webhooks (called by GePG) --------------------------------
def _xml(body: str) -> HttpResponse:
    return HttpResponse(body, content_type="application/xml", status=200)


@csrf_exempt
@require_POST
def payment_notification(request):
    """Receive a GePG payment notification and return a signed acknowledgement."""
    ack = process_payment_notification(request.body.decode("utf-8"))
    return _xml(ack)


@csrf_exempt
@require_POST
def bill_response(request):
    """Receive an async GePG control-number callback and return an acknowledgement."""
    ack = handle_bill_response_callback(request.body.decode("utf-8"))
    return _xml(ack)
