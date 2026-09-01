"""Certificate views: list, worklist, issue, detail, revoke, and public verify."""

from decimal import Decimal

import pytest

from apps.billing.enums import BillStatus
from apps.billing.models import Bill
from apps.certificates.enums import CertificateStatus
from apps.certificates.models import Certificate
from apps.certificates.services import issue_certificate
from apps.identification.services import create_report, finalize_report
from apps.orders.services import add_stone, create_order
from apps.orders.tests.factories import CustomerFactory

pytestmark = pytest.mark.django_db


def _superuser(django_user_model):
    return django_user_model.objects.create_superuser("root", "r@x.com", "pw")


def _ready_stone(user, stone_type, number):
    """A stone with a finalized report and a paid bill — ready to certify."""
    order = create_order(customer=CustomerFactory(), stone_count=1, user=user)
    stone = add_stone(order, stone_type=stone_type, weight=Decimal("1.0"), user=user)
    finalize_report(create_report(stone=stone, user=user), user=user)
    Bill.objects.create(
        order=order,
        bill_number=number,
        total_amount=Decimal("1000"),
        status=BillStatus.PAID,
    )
    return stone


def test_list_requires_permission(client, django_user_model):
    user = django_user_model.objects.create_user("no", "n@x.com", "pw")
    client.force_login(user)
    assert client.get("/certificates/", SERVER_NAME="localhost").status_code == 403


def test_list_renders(client, django_user_model):
    client.force_login(_superuser(django_user_model))
    assert client.get("/certificates/", SERVER_NAME="localhost").status_code == 200


def test_worklist_renders(client, django_user_model):
    client.force_login(_superuser(django_user_model))
    resp = client.get("/certificates/worklist/", SERVER_NAME="localhost")
    assert resp.status_code == 200


def test_issue_creates_certificate(client, django_user_model, priced_stone_type):
    su = _superuser(django_user_model)
    stone = _ready_stone(su, priced_stone_type, "BILL-CV-1")
    client.force_login(su)
    resp = client.post(
        f"/certificates/stones/{stone.pk}/issue/", SERVER_NAME="localhost"
    )
    assert resp.status_code == 302
    assert Certificate.objects.filter(stone=stone).exists()


def test_detail_and_revoke(client, django_user_model, priced_stone_type):
    su = _superuser(django_user_model)
    cert = issue_certificate(_ready_stone(su, priced_stone_type, "BILL-CV-2"), user=su)
    client.force_login(su)
    resp = client.get(f"/certificates/{cert.pk}/", SERVER_NAME="localhost")
    assert resp.status_code == 200
    resp = client.post(f"/certificates/{cert.pk}/revoke/", SERVER_NAME="localhost")
    assert resp.status_code == 302
    cert.refresh_from_db()
    assert cert.status == CertificateStatus.REVOKED


def test_public_verify_logs_access(client, django_user_model, priced_stone_type):
    su = _superuser(django_user_model)
    cert = issue_certificate(_ready_stone(su, priced_stone_type, "BILL-CV-3"), user=su)
    # No login — the verification page is public.
    resp = client.get(
        f"/certificates/verify/{cert.verification_token}/", SERVER_NAME="localhost"
    )
    assert resp.status_code == 200
    assert cert.access_logs.count() == 1


def test_verify_unknown_token(client):
    resp = client.get("/certificates/verify/not-a-real-token/", SERVER_NAME="localhost")
    assert resp.status_code == 200


def test_certificate_document_renders(client, django_user_model, priced_stone_type):
    su = _superuser(django_user_model)
    cert = issue_certificate(_ready_stone(su, priced_stone_type, "BILL-CV-4"), user=su)
    client.force_login(su)
    resp = client.get(f"/certificates/{cert.pk}/print/", SERVER_NAME="localhost")
    assert resp.status_code == 200
    assert b"GEMSTONE IDENTIFICATION REPORT" in resp.content
