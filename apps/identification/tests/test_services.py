"""Identification report creation and finalization."""

import pytest

from apps.core.enums import StoneStatus
from apps.core.exceptions import ServiceError
from apps.identification.services import create_report, finalize_report
from apps.orders.tests.factories import StoneFactory

pytestmark = pytest.mark.django_db


def test_create_report_moves_stone(user):
    stone = StoneFactory()
    report = create_report(stone=stone, user=user, conclusion="Ruby")
    assert report.report_number.startswith("RPT-")
    stone.refresh_from_db()
    assert stone.status == StoneStatus.UNDER_IDENTIFICATION


def test_finalize_locks_report(user):
    report = create_report(stone=StoneFactory(), user=user)
    finalize_report(report, user=user)
    assert report.is_finalized
    assert report.identified_at is not None


def test_finalize_twice_raises(user):
    report = create_report(stone=StoneFactory(), user=user)
    finalize_report(report, user=user)
    with pytest.raises(ServiceError):
        finalize_report(report, user=user)
