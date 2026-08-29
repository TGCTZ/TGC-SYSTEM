"""Production step lifecycle."""

import pytest

from apps.core.enums import StoneStatus
from apps.core.exceptions import ServiceError
from apps.orders.tests.factories import StoneFactory
from apps.production.enums import ProductionType, QAResult
from apps.production.services import record_qa, start_production

pytestmark = pytest.mark.django_db


def test_start_production_moves_stone(user):
    prod = start_production(StoneFactory(), ProductionType.LAPIDARY, user=user)
    prod.stone.refresh_from_db()
    assert prod.stone.status == StoneStatus.IN_PRODUCTION
    assert prod.type == ProductionType.LAPIDARY


def test_record_qa_closes_step(user):
    prod = start_production(StoneFactory(), ProductionType.CARVING, user=user)
    record_qa(prod, QAResult.PASSED, user=user)
    prod.refresh_from_db()
    assert prod.qa_result == QAResult.PASSED
    assert prod.finished_at is not None


def test_record_qa_twice_raises(user):
    prod = start_production(StoneFactory(), ProductionType.SONARA, user=user)
    record_qa(prod, QAResult.PASSED, user=user)
    with pytest.raises(ServiceError):
        record_qa(prod, QAResult.FAILED, user=user)
