"""The require_permission helper."""

import pytest
from django.core.exceptions import PermissionDenied

from apps.accounts.permissions import require_permission

pytestmark = pytest.mark.django_db


def test_none_user_is_system_bypass():
    require_permission(None, "anything.at_all")


def test_missing_permission_raises(user):
    with pytest.raises(PermissionDenied):
        require_permission(user, "identification.finalize_report")


def test_superuser_passes(django_user_model):
    su = django_user_model.objects.create_superuser("root", "root@x.com", "pw")
    require_permission(su, "identification.finalize_report")
