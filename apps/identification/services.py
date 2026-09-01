"""Identification report creation and finalization."""

from django.db import transaction
from django.utils import timezone

from apps.core.exceptions import ServiceError
from apps.core.services import generate_reference_number

from .models import IdentificationReport


@transaction.atomic
def create_report(*, stone, user=None, **fields) -> IdentificationReport:
    """Create an identification report for a stone.

    Recorded after payment, so the stone's status is left unchanged. Extra keyword
    fields (species, color, refractive_index, …) are set on the report as given.
    """
    report = IdentificationReport(
        stone=stone,
        report_number=generate_reference_number(
            IdentificationReport, "report_number", "RPT"
        ),
        **fields,
    )
    if user is not None:
        report.created_by = user
        report.identified_by = user
    report.save()
    return report


@transaction.atomic
def update_report(
    report: IdentificationReport, *, user=None, **fields
) -> IdentificationReport:
    """Update a report's findings. Refuses once the report is finalized (C4)."""
    if report.is_finalized:
        raise ServiceError("A finalized report cannot be edited.")
    for name, value in fields.items():
        setattr(report, name, value)
    if user is not None:
        report.updated_by = user
    report.save()
    return report


def finalize_report(report: IdentificationReport, *, user=None) -> IdentificationReport:
    """Lock a report against further edits (C4)."""
    if report.is_finalized:
        raise ServiceError("Report is already finalized.")
    report.is_finalized = True
    report.identified_at = timezone.now()
    if user is not None:
        report.identified_by = user
        report.updated_by = user
    report.save(
        update_fields=[
            "is_finalized",
            "identified_at",
            "identified_by",
            "updated_at",
            "updated_by",
        ]
    )
    return report
