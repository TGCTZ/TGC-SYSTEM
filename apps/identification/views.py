"""Identification views.

Phase 1 (pre-payment): register each stone under its priced *type* only.
Phase 2 (post-payment): record the gemmological *findings* and finalize the report.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Count, F, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import ListView

from apps.billing.enums import BillStatus
from apps.core.exceptions import ServiceError
from apps.core.row_actions import action
from apps.orders.models import Order, Stone
from apps.orders.services import add_stone, update_stone

from .forms import FindingsForm, StoneTypeForm
from .models import IdentificationReport, InstrumentUsed
from .services import create_report, finalize_report, update_report

_REPORT_FIELDS = (
    "species",
    "variety",
    "origin",
    "shape_cut",
    "color",
    "nature_type",
    "transparency",
    "treatment",
    "optic_character",
    "dimensions",
    "refractive_index",
    "specific_gravity",
    "is_polished",
    "conclusion",
)


# --- Phase 1: type identification ------------------------------------------
class IdentificationWorklistView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Orders with stones still to register and type."""

    permission_required = "identification.add_identificationreport"
    template_name = "pages/identification/index.html"
    context_object_name = "orders"
    paginate_by = 5

    def get_queryset(self):
        qs = (
            Order.objects.select_related("customer")
            .annotate(registered=Count("stones"))
            .filter(registered__lt=F("stone_count"))
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

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        for order in ctx["orders"]:
            order.row_actions = [
                action(
                    "Identify",
                    "lucide:microscope",
                    reverse("identification:order_identify", args=[order.pk]),
                ),
            ]
        return ctx


@login_required
@permission_required("identification.add_identificationreport", raise_exception=True)
def order_identify(request, order_pk):
    """Register the next stone on an order under its priced type."""
    order = get_object_or_404(
        Order.objects.select_related("customer").prefetch_related("stones__stone_type"),
        pk=order_pk,
    )
    form = StoneTypeForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            stone = add_stone(
                order, stone_type=form.cleaned_data["stone_type"], user=request.user
            )
        except ServiceError as exc:
            form.add_error(None, str(exc))
        else:
            messages.success(
                request, f"Identified stone {stone.label} ({stone.stone_type.name})."
            )
            return redirect("identification:order_identify", order_pk=order.pk)
    return render(
        request, "pages/identification/order.html", {"order": order, "form": form}
    )


# --- Phase 2: findings (post-payment) --------------------------------------
class FindingsWorklistView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Paid stones still awaiting their gemmological findings."""

    permission_required = "identification.change_identificationreport"
    template_name = "pages/identification/findings.html"
    context_object_name = "stones"
    paginate_by = 5

    def get_queryset(self):
        qs = (
            Stone.objects.select_related("stone_type", "order__customer")
            .filter(order__bill__status=BillStatus.PAID)
            .exclude(report__is_finalized=True)
            .order_by("order__received_date", "label")
        )
        query = self.request.GET.get("q", "").strip()
        if query:
            qs = qs.filter(
                Q(label__icontains=query)
                | Q(stone_type__name__icontains=query)
                | Q(order__reference_number__icontains=query)
                | Q(order__customer__first_name__icontains=query)
                | Q(order__customer__last_name__icontains=query)
            )
        return qs


@login_required
@permission_required("identification.change_identificationreport", raise_exception=True)
def findings_edit(request, pk):
    """Record or edit a paid stone's findings (draft); finalizing is a separate step."""
    stone = get_object_or_404(
        Stone.objects.select_related("stone_type", "order"), pk=pk
    )
    bill = getattr(stone.order, "bill", None)
    if bill is None or bill.status != BillStatus.PAID:
        messages.error(request, "The bill must be paid before recording findings.")
        return redirect("identification:findings")
    report = IdentificationReport.objects.filter(stone=stone).first()
    if report is not None and report.is_finalized:
        messages.error(request, "This report is already finalized.")
        return redirect("identification:findings")

    if request.method == "POST":
        form = FindingsForm(request.POST)
    else:
        form = FindingsForm(initial=_findings_initial(stone, report))

    if request.method == "POST" and form.is_valid():
        cd = form.cleaned_data
        update_stone(
            stone, weight=cd["weight"], weight_unit=cd["weight_unit"], user=request.user
        )
        fields = {name: cd[name] for name in _REPORT_FIELDS}
        if report is None:
            report = create_report(stone=stone, user=request.user, **fields)
        else:
            update_report(report, user=request.user, **fields)
        report.instruments_used.all().hard_delete()
        for instrument in cd["instruments"]:
            InstrumentUsed.objects.create(report=report, instrument=instrument)
        messages.success(request, f"Findings saved for stone {stone.label}.")
        return redirect("identification:findings_edit", pk=stone.pk)

    return render(
        request,
        "pages/identification/findings_form.html",
        {"stone": stone, "report": report, "form": form},
    )


def _findings_initial(stone, report):
    """Seed the findings form from the stone and any draft report already saved."""
    initial = {"weight": stone.weight, "weight_unit": stone.weight_unit}
    if report is not None:
        initial["instruments"] = list(
            report.instruments_used.values_list("instrument_id", flat=True)
        )
        for name in _REPORT_FIELDS:
            initial[name] = getattr(report, f"{name}_id", None) or getattr(report, name)
    return initial


@login_required
@permission_required("identification.finalize_report", raise_exception=True)
@require_POST
def report_finalize(request, pk):
    """Lock a findings report; the stone then becomes ready for a certificate."""
    report = get_object_or_404(IdentificationReport, pk=pk)
    try:
        finalize_report(report, user=request.user)
    except ServiceError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, f"Report {report.report_number} finalized.")
    return redirect("identification:findings")
