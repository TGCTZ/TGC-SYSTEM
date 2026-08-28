"""Enums owned by certificates."""

from django.db import models


class CertificateStatus(models.TextChoices):
    """Validity state of a certificate."""

    ISSUED = ("issued", "Issued")
    REVOKED = ("revoked", "Revoked")
    REISSUED = ("reissued", "Reissued")
