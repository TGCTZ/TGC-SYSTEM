"""Soft-delete behavior on BaseModel and its managers."""

import pytest

from apps.core.models import StoneType
from apps.core.tests.factories import StoneTypeFactory

pytestmark = pytest.mark.django_db


def test_delete_sets_deleted_at_and_keeps_row():
    st = StoneTypeFactory()
    st.delete()
    assert st.deleted_at is not None
    assert st.is_deleted
    assert StoneType.all_objects.filter(pk=st.pk).exists()


def test_default_manager_hides_deleted():
    st = StoneTypeFactory()
    st.delete()
    assert not StoneType.objects.filter(pk=st.pk).exists()
    assert StoneType.all_objects.filter(pk=st.pk).exists()


def test_restore_clears_deletion():
    st = StoneTypeFactory()
    st.delete()
    st.restore()
    assert st.deleted_at is None
    assert not st.is_deleted
    assert StoneType.objects.filter(pk=st.pk).exists()


def test_queryset_bulk_delete_is_soft():
    StoneTypeFactory.create_batch(3)
    StoneType.objects.all().delete()
    assert StoneType.objects.count() == 0
    assert StoneType.all_objects.count() == 3


def test_hard_delete_removes_row():
    st = StoneTypeFactory()
    pk = st.pk
    st.hard_delete()
    assert not StoneType.all_objects.filter(pk=pk).exists()
