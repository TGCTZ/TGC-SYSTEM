"""User-management module: services and view permission gating."""

import pytest

from django.contrib.auth.models import Group

from apps.accounts.services import create_user, set_active
from apps.accounts.tests.factories import UserFactory
from apps.core.exceptions import ServiceError

pytestmark = pytest.mark.django_db


def test_create_user_sets_password_and_groups():
    group = Group.objects.create(name="ops")
    user = create_user(
        username="jo",
        email="jo@example.com",
        first_name="Jo",
        last_name="Bloggs",
        password="a-strong-pw-9271",
        groups=[group],
        is_active=True,
    )
    assert user.check_password("a-strong-pw-9271")
    assert group in user.groups.all()


def test_cant_deactivate_self():
    user = UserFactory()
    with pytest.raises(ServiceError):
        set_active(user, False, actor=user)


def test_user_list_requires_permission(client, django_user_model):
    # A persisted usable password keeps force_login's session-auth-hash valid.
    user = django_user_model.objects.create_user("noperms", "n@x.com", "pw")
    client.force_login(user)
    resp = client.get("/users/", SERVER_NAME="localhost")
    assert resp.status_code == 403


def test_user_list_renders_with_permission(client, django_user_model):
    su = django_user_model.objects.create_superuser("root", "root@x.com", "pw")
    client.force_login(su)
    resp = client.get("/users/", SERVER_NAME="localhost")
    assert resp.status_code == 200
