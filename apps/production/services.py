"""Production step lifecycle."""

from django.db import transaction
from django.utils import timezone

from apps.core.enums import StoneStatus
from apps.core.exceptions import ServiceError
from apps.orders.services import transition_stone

from .enums import QAResult
from .models import Production


@transaction.atomic
def start_production(stone, production_type, *, assigned_to=None, user=None) -> Production:
    """Open a production step for a stone and move it into production (B1 multiple)."""
    production = Production(
        stone=stone,
        type=production_type,
        assigned_to=assigned_to,
        started_at=timezone.now(),
    )
    if user is not None:
        production.created_by = user
    production.save()
    transition_stone(
        stone, StoneStatus.IN_PRODUCTION, user=user, note=f"Started {production_type}"
    )
    return production


def record_qa(production: Production, result: str, *, qa_by=None, user=None) -> Production:
    """Record the QA outcome and close the production step."""
    if production.qa_result != QAResult.PENDING:
        raise ServiceError("QA has already been recorded for this step.")
    production.qa_result = result
    production.qa_by = qa_by
    production.finished_at = timezone.now()
    if user is not None:
        production.updated_by = user
    production.save(
        update_fields=["qa_result", "qa_by", "finished_at", "updated_at", "updated_by"]
    )
    return production
