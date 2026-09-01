"""Admin-panel registrations for core reference data.

Only the simple, safe lookup/reference models are registered here, so the generic
``/manage/`` admin can manage them out of the box. Workflow models (orders, stones,
production, bills) are deliberately left to their bespoke, service-driven flows —
their state machines must not be bypassed by generic create/edit forms.
"""

from apps.adminpanel.panels import ModelPanel
from apps.adminpanel.registry import site

from .models import (
    Instrument,
    Origin,
    ShapeCut,
    Species,
    StonePrice,
    StoneType,
    Variety,
)


class _ReferencePanel(ModelPanel):
    """Shared config for name-based lookups (see core.models.ReferenceModel)."""

    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
    ordering = ("name",)
    icon = "lucide:tag"


class StoneTypePanel(_ReferencePanel):
    """Stone types carry a pricing category."""

    list_display = ("name", "category", "is_active")
    list_filter = ("category", "is_active")


class VarietyPanel(_ReferencePanel):
    """Varieties belong to a species."""

    list_display = ("name", "species", "is_active")


class StonePricePanel(ModelPanel):
    """Fixed price per stone type."""

    list_display = ("stone_type", "price")
    search_fields = ("stone_type__name",)
    ordering = ("stone_type__name",)
    icon = "lucide:banknote"


site.register(StoneType, StoneTypePanel)
site.register(Species, _ReferencePanel)
site.register(Variety, VarietyPanel)
site.register(Origin, _ReferencePanel)
site.register(ShapeCut, _ReferencePanel)
site.register(Instrument, _ReferencePanel)
site.register(StonePrice, StonePricePanel)
