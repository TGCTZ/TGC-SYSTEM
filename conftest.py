"""Shared pytest fixtures."""

import pytest


@pytest.fixture
def user(db):
    """A saved application user."""
    from apps.accounts.tests.factories import UserFactory

    return UserFactory()


@pytest.fixture
def priced_stone_type(db):
    """A stone type with an active price."""
    from apps.core.tests.factories import StonePriceFactory

    return StonePriceFactory().stone_type
