"""Certificate issuance and revocation."""

import secrets

from django.db import transaction
from django.utils import timezone

from apps.billing.enums import BillStatus
from apps.billing.models import Bill
from apps.core.enums import StoneStatus
from apps.core.exceptions import ServiceError
from apps.core.services import generate_reference_number
from apps.identification.models import IdentificationReport
from apps.orders.services import transition_stone

from .enums import CertificateStatus
from .models import Certificate


@transaction.atomic
def issue_certificate(stone, *, user=None) -> Certificate:
    """Issue a certificate for a stone once its report is final and bill is paid.

    Requires a finalized identification report and a fully paid bill (B4). Snapshot
    fields freeze the report data at issue time.
    """
    if Certificate.objects.filter(stone=stone).exists():
        raise ServiceError("Stone already has a certificate.")

    report = IdentificationReport.objects.filter(stone=stone).first()
    if report is None or not report.is_finalized:
        raise ServiceError("Stone has no finalized identification report.")

    bill = Bill.objects.filter(order=stone.order).first()
    if bill is None or bill.status != BillStatus.PAID:
        raise ServiceError("Stone's bill must be fully paid before certification.")

    gemmologist = ""
    if report.identified_by is not None:
        gemmologist = report.identified_by.get_full_name() or report.identified_by.username

    certificate = Certificate(
        stone=stone,
        report=report,
        certificate_no=generate_reference_number(Certificate, "certificate_no", "CERT"),
        verification_token=secrets.token_hex(32),
        stone_type_snapshot=stone.stone_type.name,
        weight_snapshot=stone.weight,
        color_snapshot=report.get_color_display() if report.color else "",
        origin_snapshot=report.origin.name if report.origin else "",
        gemmologist=gemmologist,
        status=CertificateStatus.ISSUED,
        issued_by=user,
        issued_at=timezone.now(),
    )
    if user is not None:
        certificate.created_by = user
    certificate.save()

    transition_stone(stone, StoneStatus.CERTIFIED, user=user, note=f"Certified {certificate.certificate_no}")
    return certificate


def revoke_certificate(certificate: Certificate, *, user=None) -> Certificate:
    """Revoke a certificate (C3)."""
    if certificate.status == CertificateStatus.REVOKED:
        raise ServiceError("Certificate is already revoked.")
    certificate.status = CertificateStatus.REVOKED
    if user is not None:
        certificate.updated_by = user
    certificate.save(update_fields=["status", "updated_at", "updated_by"])
    return certificate
