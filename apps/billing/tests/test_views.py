"""Billing staff views: list, worklist, generate, and detail."""

from decimal import Decimal

import pytest

from apps.billing import services as billing_services
from apps.billing.models import Bill, Payment
from apps.billing.services import generate_bill_for_order
from apps.orders.services import add_stone, create_order
from apps.orders.tests.factories import CustomerFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def no_gepg(monkeypatch):
    """Stub GePG submission so bill generation stays offline (returns a control no)."""
    monkeypatch.setattr(
        billing_services,
        "submit_bill",
        lambda bill, customer, username: {
            "success": True,
            "control_number": "994400000123",
            "status_code": "7101",
            "status_desc": "ok",
            "is_sync": True,
            "raw_response": "<x/>",
        },
    )


def _billable_order(user, stone_type):
    order = create_order(customer=CustomerFactory(), stone_count=1, user=user)
    add_stone(order, stone_type=stone_type, weight=Decimal("2.0"), user=user)
    return order


def _superuser(django_user_model):
    return django_user_model.objects.create_superuser("root", "r@x.com", "pw")


def test_bill_list_requires_permission(client, django_user_model):
    user = django_user_model.objects.create_user("no", "n@x.com", "pw")
    client.force_login(user)
    resp = client.get("/billing/", SERVER_NAME="localhost")
    assert resp.status_code == 403


def test_bill_list_renders(client, django_user_model):
    client.force_login(_superuser(django_user_model))
    assert client.get("/billing/", SERVER_NAME="localhost").status_code == 200


def test_worklist_renders(client, django_user_model):
    client.force_login(_superuser(django_user_model))
    assert client.get("/billing/worklist/", SERVER_NAME="localhost").status_code == 200


def test_generate_creates_bill_and_redirects(
    client, django_user_model, priced_stone_type, no_gepg
):
    su = _superuser(django_user_model)
    order = _billable_order(su, priced_stone_type)
    client.force_login(su)
    resp = client.post(f"/billing/orders/{order.pk}/generate/", SERVER_NAME="localhost")
    assert resp.status_code == 302
    bill = Bill.objects.get(order=order)
    assert resp["Location"] == f"/billing/{bill.pk}/"


def test_bill_detail_renders(client, django_user_model, priced_stone_type, no_gepg):
    su = _superuser(django_user_model)
    bill = generate_bill_for_order(_billable_order(su, priced_stone_type), user=su)
    client.force_login(su)
    resp = client.get(f"/billing/{bill.pk}/", SERVER_NAME="localhost")
    assert resp.status_code == 200


def test_payments_feed_requires_permission(client, django_user_model):
    user = django_user_model.objects.create_user("no", "n@x.com", "pw")
    client.force_login(user)
    resp = client.get("/billing/payments/", SERVER_NAME="localhost")
    assert resp.status_code == 403


def test_payments_feed_renders(client, django_user_model):
    client.force_login(_superuser(django_user_model))
    resp = client.get("/billing/payments/", SERVER_NAME="localhost")
    assert resp.status_code == 200


def test_payment_detail_renders(client, django_user_model):
    payment = Payment.objects.create(
        pyr_name="Ida", paid_amount=Decimal("100"), trx_id="TRX-D1"
    )
    client.force_login(_superuser(django_user_model))
    resp = client.get(f"/billing/payments/{payment.pk}/", SERVER_NAME="localhost")
    assert resp.status_code == 200
