"""Admin registrations for billing."""

from django.contrib import admin

from apps.core.admin import BaseModelAdmin

from .models import Bill, BillItem, Payment, ServiceProvider


class BillItemInline(admin.TabularInline):
    """Line items shown inline on the bill page."""

    model = BillItem
    extra = 0
    fields = ("stone", "description", "unit_price", "weight", "amount")


class PaymentInline(admin.TabularInline):
    """Payments shown inline on the bill page."""

    model = Payment
    extra = 0
    fields = ("amount", "paid_at", "channel", "reference")


@admin.register(ServiceProvider)
class ServiceProviderAdmin(BaseModelAdmin):
    """Admin for GePG service providers."""

    list_display = ("name", "sp_code", "is_active", "deleted_at")
    search_fields = ("name", "sp_code")


@admin.register(Bill)
class BillAdmin(BaseModelAdmin):
    """Admin for bills."""

    list_display = ("bill_number", "order", "total_amount", "status", "control_number")
    list_filter = ("status", "currency")
    search_fields = ("bill_number", "control_number", "order__reference_no")
    list_select_related = ("order",)
    inlines = [BillItemInline, PaymentInline]
