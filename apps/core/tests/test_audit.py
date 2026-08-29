"""Actor columns and change-history logging."""

import pytest
from auditlog.models import LogEntry

from apps.core.current_user import reset_current_user, set_current_user
from apps.core.models import StoneType
from apps.core.tests.factories import StoneTypeFactory

pytestmark = pytest.mark.django_db


def test_save_sets_actor_from_current_user(user):
    token = set_current_user(user)
    try:
        st = StoneType.objects.create(name="AuditTest", category="precious")
    finally:
        reset_current_user(token)
    assert st.created_by == user
    assert st.updated_by == user


def test_auditlog_records_field_change():
    st = StoneTypeFactory()
    st.name = "Changed"
    st.save()
    changes = [le.changes for le in LogEntry.objects.get_for_object(st)]
    assert any("name" in c for c in changes)
