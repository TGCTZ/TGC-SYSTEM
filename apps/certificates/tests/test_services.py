"""Certificate issuance and revocation."""

from decimal import Decimal

import pytest

from apps.billing.enums import BillStatus
from apps.billing.models import Bill
from apps.certificates.enums import CertificateStatus
from apps.certificates.services import issue_certificate, revoke_certificate
from apps.core.enums import StoneStatus
from apps.core.exceptions import ServiceError
from apps.identification.services import create_report, finalize_report
from apps.orders.services import add_stone, create_order
from apps.orders.tests.factories import CustomerFactory

pytestmark = pytest.mark.django_db


def _stone(user, stone_type):
    order = create_order(customer=CustomerFactory(), stone_count=1, user=user)
    return add_stone(order, stone_type=stone_type, weight=Decimal("1.0"), user=user)


def _bill(order, status, number):
    return Bill.objects.create(
        order=order, bill_number=number, total_amount=Decimal("1000"), status=status
    )


def _ready_stone(user, stone_type, number):
    """A stone with a finalized report and a paid bill."""
    stone = _stone(user, stone_type)
    finalize_report(create_report(stone=stone, user=user), user=user)
    _bill(stone.order, BillStatus.PAID, number)
    return stone


def test_issue_certificate_success(user, priced_stone_type):
    stone = _ready_stone(user, priced_stone_type, "BILL-C-1")
    cert = issue_certificate(stone, user=user)
    assert cert.certificate_no.startswith("CERT-")
    assert cert.stone_type_snapshot == stone.stone_type.name
    stone.refresh_from_db()
    assert stone.status == StoneStatus.CERTIFIED


def test_issue_without_finalized_report_raises(user, priced_stone_type):
    stone = _stone(user, priced_stone_type)
    _bill(stone.order, BillStatus.PAID, "BILL-C-2")
    with pytest.raises(ServiceError):
        issue_certificate(stone, user=user)


def test_issue_when_unpaid_raises(user, priced_stone_type):
    stone = _stone(user, priced_stone_type)
    finalize_report(create_report(stone=stone, user=user), user=user)
    _bill(stone.order, BillStatus.PENDING, "BILL-C-3")
    with pytest.raises(ServiceError):
        issue_certificate(stone, user=user)


def test_issue_twice_raises(user, priced_stone_type):
    stone = _ready_stone(user, priced_stone_type, "BILL-C-4")
    issue_certificate(stone, user=user)
    with pytest.raises(ServiceError):
        issue_certificate(stone, user=user)


def test_revoke_certificate(user, priced_stone_type):
    stone = _ready_stone(user, priced_stone_type, "BILL-C-5")
    cert = issue_certificate(stone, user=user)
    revoke_certificate(cert, user=user)
    assert cert.status == CertificateStatus.REVOKED
    with pytest.raises(ServiceError):
        revoke_certificate(cert, user=user)
