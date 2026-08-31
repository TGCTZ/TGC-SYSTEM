"""Generic model-admin views over a registered reference model (core.Species)."""

import pytest

from apps.core.models import Species

pytestmark = pytest.mark.django_db


def _superuser(django_user_model):
    return django_user_model.objects.create_superuser("root", "root@x.com", "pw")


def test_dashboard_renders(client, django_user_model):
    """Smoke: KPI cards + activity feed + a card per registered model."""
    client.force_login(_superuser(django_user_model))
    resp = client.get("/manage/", SERVER_NAME="localhost")
    assert resp.status_code == 200


def test_reference_list_renders(client, django_user_model):
    client.force_login(_superuser(django_user_model))
    resp = client.get("/manage/core/species/", SERVER_NAME="localhost")
    assert resp.status_code == 200


def test_reference_create(client, django_user_model):
    client.force_login(_superuser(django_user_model))
    resp = client.post(
        "/manage/core/species/new/",
        {"name": "Corundum", "is_active": "on"},
        SERVER_NAME="localhost",
    )
    assert resp.status_code == 302
    assert Species.objects.filter(name="Corundum").exists()


def test_unregistered_model_is_404(client, django_user_model):
    client.force_login(_superuser(django_user_model))
    resp = client.get("/manage/orders/order/", SERVER_NAME="localhost")
    assert resp.status_code == 404
