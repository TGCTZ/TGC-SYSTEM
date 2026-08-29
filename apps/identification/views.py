"""Identification views: worklist, per-order identification, and finalization."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.db.models import Count, F, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import ListView

from apps.core.exceptions import ServiceError
from apps.core.row_actions import action
from apps.orders.models import Order, Stone
from apps.orders.services import add_stone, update_stone

from .forms import StoneIdentificationForm
from .models import IdentificationReport, InstrumentUsed
from .services import create_report, finalize_report, update_report

_REPORT_FIELDS = (
    "species", "variety", "origin", "shape_cut", "color", "transparency",
    "treatment", "optic_character", "refractive_index", "specific_gravity",
    "is_polished", "conclusion",
)


class WorklistView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Orders that still have stones to identify."""

    permission_required = "identification.add_identificationreport"
    template_name = "pages/identification/index.html"
    context_object_name = "orders"
    paginate_by = 5

    def get_queryset(self):
        return (
            Order.objects.select_related("customer")
            .annotate(
                finalized=Count("stones", filter=Q(stones__report__is_finalized=True))
            )
            .filter(finalized__lt=F("stone_count"))
            .order_by("received_date")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        for order in ctx["orders"]:
            order.row_actions = [
                action(
                    "Identify",
                    "lucide:microscope",
                    reverse("identification:order", args=[order.pk]),
                ),
            ]
        return ctx


@login_required
@permission_required("identification.add_identificationreport", raise_exception=True)
def order_identify(request, order_pk):
    """Register and identify one stone on an order."""
    order = get_object_or_404(
        Order.objects.select_related("customer").prefetch_related("stones__report"),
        pk=order_pk,
    )
    form = StoneIdentificationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        cd = form.cleaned_data
        try:
            with transaction.atomic():
                stone = add_stone(
                    order,
                    stone_type=cd["stone_type"],
                    weight=cd["weight"],
                    weight_unit=cd["weight_unit"],
                    user=request.user,
                )
                report = create_report(
                    stone=stone,
                    user=request.user,
                    species=cd["species"],
                    variety=cd["variety"],
                    origin=cd["origin"],
                    shape_cut=cd["shape_cut"],
                    color=cd["color"],
                    transparency=cd["transparency"],
                    treatment=cd["treatment"],
                    optic_character=cd["optic_character"],
                    refractive_index=cd["refractive_index"],
                    specific_gravity=cd["specific_gravity"],
                    is_polished=cd["is_polished"],
                    conclusion=cd["conclusion"],
                )
                for instrument in cd["instruments"]:
                    InstrumentUsed.objects.create(report=report, instrument=instrument)
        except ServiceError as exc:
            form.add_error(None, str(exc))
        else:
            messages.success(request, f"Identified stone {stone.label}.")
            return redirect("identification:order", order_pk=order.pk)

    return render(
        request, "pages/identification/order.html", {"order": order, "form": form}
    )


@login_required
@permission_required("identification.change_identificationreport", raise_exception=True)
def stone_edit(request, pk):
    """Edit a recorded stone and its (draft) identification report."""
    stone = get_object_or_404(
        Stone.objects.select_related("stone_type", "order"), pk=pk
    )
    report = IdentificationReport.objects.filter(stone=stone).first()
    if report is None:
        messages.error(request, "This stone has no identification report yet.")
        return redirect("identification:order", order_pk=stone.order_id)
    if report.is_finalized:
        messages.error(request, "Finalized reports cannot be edited.")
        return redirect("identification:order", order_pk=stone.order_id)

    if request.method == "POST":
        form = StoneIdentificationForm(request.POST)
    else:
        form = StoneIdentificationForm(initial=_edit_initial(stone, report))

    if request.method == "POST" and form.is_valid():
        cd = form.cleaned_data
        with transaction.atomic():
            update_stone(
                stone,
                stone_type=cd["stone_type"],
                weight=cd["weight"],
                weight_unit=cd["weight_unit"],
                user=request.user,
            )
            update_report(
                report,
                user=request.user,
                **{name: cd[name] for name in _REPORT_FIELDS},
            )
            report.instruments_used.all().hard_delete()
            for instrument in cd["instruments"]:
                InstrumentUsed.objects.create(report=report, instrument=instrument)
        messages.success(request, f"Updated stone {stone.label}.")
        return redirect("identification:order", order_pk=stone.order_id)

    return render(request, "pages/identification/edit.html", {"stone": stone, "form": form})


def _edit_initial(stone, report):
    initial = {
        "stone_type": stone.stone_type_id,
        "weight": stone.weight,
        "weight_unit": stone.weight_unit,
        "instruments": list(
            report.instruments_used.values_list("instrument_id", flat=True)
        ),
    }
    for name in _REPORT_FIELDS:
        initial[name] = getattr(report, f"{name}_id", None) or getattr(report, name)
    return initial


@login_required
@permission_required("identification.finalize_report", raise_exception=True)
@require_POST
def finalize(request, pk):
    """Lock an identification report."""
    report = get_object_or_404(IdentificationReport, pk=pk)
    try:
        finalize_report(report, user=request.user)
    except ServiceError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, f"Report {report.report_number} finalized.")
    return redirect("identification:order", order_pk=report.stone.order_id)
