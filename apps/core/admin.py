"""Admin registrations for core reference data and pricing."""

from django.contrib import admin

from .models import (
    Instrument,
    Origin,
    ShapeCut,
    Species,
    StonePrice,
    StoneType,
    Variety,
)

AUDIT_FIELDS = (
    "created_at",
    "created_by",
    "updated_at",
    "updated_by",
    "deleted_at",
    "deleted_by",
)


class BaseModelAdmin(admin.ModelAdmin):
    """Shared admin: shows soft-deleted rows and locks audit fields."""

    readonly_fields = AUDIT_FIELDS

    def get_queryset(self, request):
        """Include soft-deleted rows so staff can view and restore them."""
        return self.model.all_objects.all()


class ReferenceAdmin(BaseModelAdmin):
    """Admin for simple name-based lookups."""

    list_display = ("name", "is_active", "deleted_at")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(StoneType)
class StoneTypeAdmin(ReferenceAdmin):
    """Admin for stone types."""

    list_display = ("name", "category", "is_active", "deleted_at")
    list_filter = ("category", "is_active")


@admin.register(Variety)
class VarietyAdmin(ReferenceAdmin):
    """Admin for varieties."""

    list_display = ("name", "species", "is_active", "deleted_at")
    list_filter = ("is_active", "species")
    list_select_related = ("species",)


@admin.register(StonePrice)
class StonePriceAdmin(BaseModelAdmin):
    """Admin for stone prices."""

    list_display = ("stone_type", "price_per_unit", "unit", "is_active", "deleted_at")
    list_filter = ("unit", "is_active")
    search_fields = ("stone_type__name",)
    list_select_related = ("stone_type",)


admin.site.register([Species, Origin, ShapeCut, Instrument], ReferenceAdmin)
