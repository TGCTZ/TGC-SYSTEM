"""Admin registrations for certificates."""

from django.contrib import admin

from apps.core.admin import BaseModelAdmin

from .models import Certificate, CertificateAccessLog


@admin.register(Certificate)
class CertificateAdmin(BaseModelAdmin):
    """Admin for certificates."""

    list_display = ("certificate_no", "stone", "status", "issued_at", "issued_by")
    list_filter = ("status",)
    search_fields = ("certificate_no", "stone__order__reference_no")
    list_select_related = ("stone", "issued_by")


@admin.register(CertificateAccessLog)
class CertificateAccessLogAdmin(admin.ModelAdmin):
    """Read-only view of certificate verification hits."""

    list_display = ("certificate", "accessed_at", "ip_address")
    readonly_fields = ("certificate", "accessed_at", "ip_address", "user_agent")
