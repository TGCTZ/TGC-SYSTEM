"""Reception views: order list, detail, and creation."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import redirect, render
from django.views.generic import DetailView, ListView

from .models import Customer, Order
from .services import create_order


class OrderListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Searchable, paginated list of orders."""

    permission_required = "orders.view_order"
    template_name = "pages/orders/index.html"
    context_object_name = "orders"
    paginate_by = 20

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
        return ctx


class OrderDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Order detail with its (identified) stones."""

    permission_required = "orders.view_order"
    template_name = "pages/orders/show.html"
    context_object_name = "order"

    def get_queryset(self):
        return Order.objects.select_related("customer").prefetch_related(
            "stones__stone_type"
        )


@login_required
@permission_required("orders.add_order", raise_exception=True)
def order_create(request):
    """Register a customer and an order with its stone count."""
    if request.method == "POST":
        first = request.POST.get("first_name", "").strip()
        last = request.POST.get("last_name", "").strip()
        phone = request.POST.get("phone", "").strip()
        try:
            stone_count = int(request.POST.get("stone_count", "0"))
        except ValueError:
            stone_count = 0

        if not (first and last and phone):
            messages.error(request, "First name, last name, and phone are required.")
        elif stone_count < 1:
            messages.error(request, "Number of stones must be at least 1.")
        else:
            with transaction.atomic():
                customer = Customer.objects.create(
                    first_name=first,
                    middle_name=request.POST.get("middle_name", "").strip(),
                    last_name=last,
                    phone=phone,
                    email=request.POST.get("email", "").strip(),
                    region=request.POST.get("region", "").strip(),
                )
                order = create_order(
                    customer=customer, stone_count=stone_count, user=request.user
                )
            messages.success(request, f"Order {order.reference_no} created.")
            return redirect("orders:detail", pk=order.pk)

    return render(request, "pages/orders/form.html")
