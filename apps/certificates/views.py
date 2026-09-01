"""Certificate views: issue worklist, list, detail, revoke, and public verification."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import ListView

from apps.billing.enums import BillStatus
from apps.core.exceptions import ServiceError
from apps.core.row_actions import action
from apps.orders.models import Stone

from .enums import CertificateStatus
from .models import Certificate, CertificateAccessLog
from .services import issue_certificate, revoke_certificate

# Certificate status -> badge variant for the UI.
_STATUS_VARIANT = {
    CertificateStatus.ISSUED: "success",
    CertificateStatus.REVOKED: "danger",
    CertificateStatus.REISSUED: "info",
}


class CertificateListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Searchable, filterable, paginated list of issued certificates."""

    permission_required = "certificates.view_certificate"
    template_name = "pages/certificates/index.html"
    context_object_name = "certificates"
    paginate_by = 5

    def get_queryset(self):
        qs = Certificate.objects.select_related("stone__order__customer").order_by(
            "-issued_at"
        )
        query = self.request.GET.get("q", "").strip()
        if query:
            qs = qs.filter(
                Q(certificate_no__icontains=query)
                | Q(status__icontains=query)
                | Q(stone_type_snapshot__icontains=query)
                | Q(stone__label__icontains=query)
                | Q(stone__order__reference_no__icontains=query)
                | Q(stone__order__customer__first_name__icontains=query)
                | Q(stone__order__customer__last_name__icontains=query)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["can_issue"] = self.request.user.has_perm("certificates.issue_certificate")
        for cert in ctx["certificates"]:
            cert.status_variant = _STATUS_VARIANT.get(cert.status, "info")
            cert.row_actions = [
                action(
                    "View", "lucide:eye", reverse("certificates:detail", args=[cert.pk])
                )
            ]
        return ctx


class CertifiableStonesView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Stones ready to certify: finalized report, paid bill, and no certificate yet."""

    permission_required = "certificates.issue_certificate"
    template_name = "pages/certificates/worklist.html"
    context_object_name = "stones"
    paginate_by = 5

    def get_queryset(self):
        qs = Stone.objects.select_related("stone_type", "order__customer").filter(
            report__is_finalized=True,
            order__bill__status=BillStatus.PAID,
            certificate__isnull=True,
        )
        query = self.request.GET.get("q", "").strip()
        if query:
            qs = qs.filter(
                Q(order__reference_no__icontains=query)
                | Q(order__customer__first_name__icontains=query)
                | Q(order__customer__last_name__icontains=query)
                | Q(order__customer__company_name__icontains=query)
            )
        return qs.order_by("order__received_date", "label")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["query"] = self.request.GET.get("q", "")
        return ctx


@login_required
@permission_required("certificates.issue_certificate", raise_exception=True)
@require_POST
def issue(request, stone_pk):
    """Issue a certificate for a stone (validates report + payment in the service)."""
    stone = get_object_or_404(Stone, pk=stone_pk)
    try:
        certificate = issue_certificate(stone, user=request.user)
    except ServiceError as exc:
        messages.error(request, str(exc))
        return redirect("certificates:worklist")
    messages.success(request, f"Certificate {certificate.certificate_no} issued.")
    return redirect("certificates:detail", pk=certificate.pk)


@login_required
@permission_required("certificates.view_certificate", raise_exception=True)
def detail(request, pk):
    """Certificate detail: snapshot data, verification link, and access log."""
    certificate = get_object_or_404(
        Certificate.objects.select_related("stone__order__customer", "issued_by"), pk=pk
    )
    return render(
        request,
        "pages/certificates/detail.html",
        {
            "certificate": certificate,
            "status_variant": _STATUS_VARIANT.get(certificate.status, "info"),
            "verify_url": request.build_absolute_uri(
                reverse("certificates:verify", args=[certificate.verification_token])
            ),
            "access_logs": certificate.access_logs.all()[:20],
            "can_revoke": (
                request.user.has_perm("certificates.revoke_certificate")
                and certificate.status != CertificateStatus.REVOKED
            ),
        },
    )


@login_required
@permission_required("certificates.view_certificate", raise_exception=True)
def print_certificate(request, pk):
    """Printable gemstone-identification-report document for a certificate."""
    certificate = get_object_or_404(
        Certificate.objects.select_related(
            "stone__order__customer",
            "report__species",
            "report__variety",
            "report__origin",
            "report__shape_cut",
            "issued_by",
        ),
        pk=pk,
    )
    return render(
        request,
        "pages/certificates/print.html",
        {
            "certificate": certificate,
            "report": certificate.report,
            "instruments": certificate.report.instruments_used.select_related(
                "instrument"
            ),
            "verify_url": request.build_absolute_uri(
                reverse("certificates:verify", args=[certificate.verification_token])
            ),
        },
    )


@login_required
@permission_required("certificates.revoke_certificate", raise_exception=True)
@require_POST
def revoke(request, pk):
    """Revoke a certificate."""
    certificate = get_object_or_404(Certificate, pk=pk)
    try:
        revoke_certificate(certificate, user=request.user)
    except ServiceError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, f"Certificate {certificate.certificate_no} revoked.")
    return redirect("certificates:detail", pk=certificate.pk)


def verify(request, token):
    """Public certificate verification — no login. Logs each access."""
    certificate = (
        Certificate.objects.select_related("stone__order__customer")
        .filter(verification_token=token)
        .first()
    )
    if certificate is not None:
        CertificateAccessLog.objects.create(
            certificate=certificate,
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:255],
        )
    return render(
        request,
        "pages/certificates/verify.html",
        {
            "certificate": certificate,
            "valid": certificate is not None
            and certificate.status != CertificateStatus.REVOKED,
        },
    )
