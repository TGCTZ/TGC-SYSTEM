"""Admin registrations for identification."""

from django.contrib import admin

from apps.core.admin import BaseModelAdmin

from .models import IdentificationReport, InstrumentUsed


class InstrumentUsedInline(admin.TabularInline):
    """Instruments shown inline on the report page."""

    model = InstrumentUsed
    extra = 0
    fields = ("instrument", "reading")


@admin.register(IdentificationReport)
class IdentificationReportAdmin(BaseModelAdmin):
    """Admin for identification reports."""

    list_display = ("report_number", "stone", "species", "is_finalized", "identified_at")
    list_filter = ("is_finalized", "treatment", "transparency")
    search_fields = ("report_number", "stone__order__reference_no")
    list_select_related = ("stone", "species")
    inlines = [InstrumentUsedInline]
