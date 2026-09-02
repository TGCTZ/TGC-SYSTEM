"""Roles & permissions portal: GroupForm logic and views."""

import pytest

from django.contrib.auth.models import Group, Permission

from apps.accounts.tests.factories import UserFactory
from apps.backoffice.roles import GroupForm

pytestmark = pytest.mark.django_db


def test_group_form_creates_with_perms_and_members():
    user = UserFactory()
    # The matrix (and thus the permissions field) only offers business perms.
    perm = Permission.objects.get(
        content_type__app_label="accounts", codename="view_user"
    )
    form = GroupForm(
        {"name": "editors", "permissions": [perm.pk], "members": [user.pk]}
    )
    assert form.is_valid(), form.errors
    group = form.save()
    assert perm in group.permissions.all()
    assert user in group.user_set.all()


def test_group_form_preserves_non_business_perms():
    """Editing via the matrix must keep perms it never renders (e.g. auth.*_group)."""
    group = Group.objects.create(name="admins")
    infra = Permission.objects.get(
        content_type__app_label="auth", codename="view_group"
    )
    business = Permission.objects.get(
        content_type__app_label="accounts", codename="view_user"
    )
    group.permissions.set([infra])
    form = GroupForm(
        {"name": "admins", "permissions": [business.pk], "members": []},
        instance=group,
    )
    assert form.is_valid(), form.errors
    form.save()
    perms = set(group.permissions.all())
    assert infra in perms  # preserved though the matrix never rendered it
    assert business in perms


def test_role_create_view(client, django_user_model):
    su = django_user_model.objects.create_superuser("root", "root@x.com", "pw")
    client.force_login(su)
    resp = client.post(
        "/backoffice/roles/new/",
        {"name": "reviewers", "permissions": [], "members": []},
        SERVER_NAME="localhost",
    )
    assert resp.status_code == 302
    assert Group.objects.filter(name="reviewers").exists()


def test_role_form_renders(client, django_user_model):
    """Smoke: the create form renders the permission matrix + users toggle-table."""
    su = django_user_model.objects.create_superuser("root", "root@x.com", "pw")
    client.force_login(su)
    resp = client.get("/backoffice/roles/new/", SERVER_NAME="localhost")
    assert resp.status_code == 200


def test_role_list_requires_permission(client, django_user_model):
    # A persisted usable password keeps force_login's session-auth-hash valid.
    user = django_user_model.objects.create_user("noperms", "n@x.com", "pw")
    client.force_login(user)
    resp = client.get("/backoffice/roles/", SERVER_NAME="localhost")
    assert resp.status_code == 403
