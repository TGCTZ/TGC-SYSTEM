"""Admin registrations for orders."""

from django.contrib import admin

from apps.core.admin import BaseModelAdmin

from .models import Customer, Order, StatusHistory, Stone


class StoneInline(admin.TabularInline):
    """Stones shown inline on the order page."""

    model = Stone
    extra = 0
    fields = ("label", "stone_type", "weight", "weight_unit", "quantity", "status")


@admin.register(Customer)
class CustomerAdmin(BaseModelAdmin):
    """Admin for customers."""

    list_display = ("full_name", "phone", "company_name", "region", "deleted_at")
    search_fields = ("first_name", "last_name", "phone", "company_name")


@admin.register(Order)
class OrderAdmin(BaseModelAdmin):
    """Admin for orders."""

    list_display = ("reference_no", "customer", "received_date", "stone_count")
    search_fields = ("reference_no", "customer__first_name", "customer__last_name")
    list_select_related = ("customer",)
    inlines = [StoneInline]


@admin.register(Stone)
class StoneAdmin(BaseModelAdmin):
    """Admin for stones."""

    list_display = ("__str__", "stone_type", "weight", "weight_unit", "status")
    list_filter = ("status", "stone_type")
    search_fields = ("order__reference_no", "label")
    list_select_related = ("order", "stone_type")


@admin.register(StatusHistory)
class StatusHistoryAdmin(admin.ModelAdmin):
    """Read-only view of the status audit trail."""

    list_display = ("stone", "from_status", "to_status", "changed_by", "changed_at")
    list_filter = ("to_status",)
    readonly_fields = (
        "stone",
        "from_status",
        "to_status",
        "changed_by",
        "changed_at",
        "note",
    )
