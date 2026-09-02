"""Certificate (one per stone) and its public-access log."""

from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.core.models import BaseModel

from ..enums import CertificateStatus


class Certificate(BaseModel):
    """A certificate for one stone. Snapshot fields freeze the report data."""

    stone = models.OneToOneField(
        "orders.Stone", on_delete=models.PROTECT, related_name="certificate"
    )
    report = models.ForeignKey(
        "identification.IdentificationReport",
        on_delete=models.PROTECT,
        related_name="certificates",
    )
    certificate_number = models.CharField(max_length=30)
    verification_token = models.CharField(max_length=64)

    # Snapshot of report data at issue time (intentionally frozen).
    stone_type_snapshot = models.CharField(max_length=100)
    weight_snapshot = models.DecimalField(max_digits=10, decimal_places=3)
    color_snapshot = models.CharField(max_length=100, blank=True, default="")
    origin_snapshot = models.CharField(max_length=100, blank=True, default="")
    gemmologist = models.CharField(max_length=100, blank=True, default="")

    # Artifacts.
    qr_code = models.CharField(max_length=100, blank=True, default="")
    pdf_file = models.CharField(max_length=100, blank=True, default="")

    status = models.CharField(
        max_length=20,
        choices=CertificateStatus.choices,
        default=CertificateStatus.ISSUED,
    )
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    issued_at = models.DateTimeField()

    class Meta:
        ordering = ["-issued_at"]
        permissions = [
            ("issue_certificate", "Can issue a certificate"),
            ("revoke_certificate", "Can revoke a certificate"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["certificate_number"],
                condition=Q(deleted_at__isnull=True),
                name="unique_active_certificate_number",
            ),
            models.UniqueConstraint(
                fields=["verification_token"],
                condition=Q(deleted_at__isnull=True),
                name="unique_active_verification_token",
            ),
        ]

    def __str__(self) -> str:
        return self.certificate_number


class CertificateAccessLog(models.Model):
    """Append-only log of public certificate verifications."""

    certificate = models.ForeignKey(
        Certificate, on_delete=models.CASCADE, related_name="access_logs"
    )
    accessed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["-accessed_at"]

    def __str__(self) -> str:
        return f"{self.certificate} @ {self.accessed_at:%Y-%m-%d %H:%M}"
