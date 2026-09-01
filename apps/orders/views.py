"""Reception views: order list, detail, and creation."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import DetailView, ListView

from apps.core.row_actions import action

from .forms import OrderCreateForm
from .models import Customer, Order
from .services import create_order


class OrderListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Searchable, paginated list of orders."""

    permission_required = "orders.view_order"
    template_name = "pages/orders/index.html"
    context_object_name = "orders"
    paginate_by = 5

    def get_queryset(self):
        qs = (
            Order.objects.select_related("customer")
            .annotate(identified=Count("stones"))
            .order_by("-received_date")
        )
        query = self.request.GET.get("q", "").strip()
        if query:
            qs = qs.filter(
                Q(reference_no__icontains=query)
                | Q(customer__first_name__icontains=query)
                | Q(customer__last_name__icontains=query)
                | Q(customer__phone__icontains=query)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["query"] = self.request.GET.get("q", "")
        for order in ctx["orders"]:
            order.row_actions = [
                action("View", "lucide:eye", reverse("orders:detail", args=[order.pk])),
            ]
        return ctx


class OrderDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Order detail with its (identified) stones."""

    permission_required = "orders.view_order"
    template_name = "pages/orders/show.html"
    context_object_name = "order"

    def get_queryset(self):
        return Order.objects.select_related("customer").prefetch_related(
            "stones__stone_type", "stones__report"
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        for stone in self.object.stones.all():
            stone.row_actions = self._stone_actions(stone)
        return ctx

    def _stone_actions(self, stone):
        """Build the permission-filtered action list for one stone row."""
        try:
            report = stone.report
        except ObjectDoesNotExist:
            report = None
        user, actions = self.request.user, []
        finalized = report is not None and report.is_finalized
        change = "identification.change_identificationreport"
        if not finalized and user.has_perm(change):
            actions.append(
                action(
                    "Findings",
                    "lucide:clipboard-list",
                    reverse("identification:findings_stone", args=[stone.pk]),
                )
            )
        if (
            report is not None
            and not finalized
            and user.has_perm("identification.finalize_report")
        ):
            actions.append(
                action(
                    "Finalize",
                    "lucide:lock",
                    reverse("identification:finalize", args=[report.pk]),
                    method="post",
                )
            )
        return actions


@login_required
@permission_required("orders.add_order", raise_exception=True)
def order_create(request):
    """Register a customer and an order with its stone count."""
    form = OrderCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        cd = form.cleaned_data
        with transaction.atomic():
            customer = Customer.objects.create(
                first_name=cd["first_name"],
                middle_name=cd["middle_name"],
                last_name=cd["last_name"],
                phone=cd["phone"],
                email=cd["email"],
                region=cd["region"],
            )
            order = create_order(
                customer=customer, stone_count=cd["stone_count"], user=request.user
            )
        messages.success(request, f"Order {order.reference_no} created.")
        return redirect("orders:detail", pk=order.pk)

    return render(request, "pages/orders/form.html", {"form": form})
