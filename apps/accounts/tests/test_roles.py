"""The setup_roles management command."""

import pytest
from django.contrib.auth.models import Group
from django.core.management import call_command

from apps.accounts.roles import ROLE_PERMISSIONS

pytestmark = pytest.mark.django_db


def test_creates_all_groups():
    call_command("setup_roles")
    for name in ROLE_PERMISSIONS:
        assert Group.objects.filter(name=name).exists()


def test_idempotent():
    call_command("setup_roles")
    call_command("setup_roles")
    assert Group.objects.filter(name="gemmologist").count() == 1


def test_role_grants_expected_permission(user):
    call_command("setup_roles")
    user.groups.add(Group.objects.get(name="gemmologist"))
    user = type(user).objects.get(pk=user.pk)  # reset the permission cache
    assert user.has_perm("identification.finalize_report")
    assert not user.has_perm("billing.generate_bill")
