"""Admin registrations for production."""

from django.contrib import admin

from apps.core.admin import BaseModelAdmin

from .models import Production


@admin.register(Production)
class ProductionAdmin(BaseModelAdmin):
    """Admin for production steps."""

    list_display = ("stone", "type", "assigned_to", "qa_result", "finished_at")
    list_filter = ("type", "qa_result")
    search_fields = ("stone__order__reference_no",)
    list_select_related = ("stone", "assigned_to")
