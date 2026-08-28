"""Factories for production."""

import factory
from factory.fuzzy import FuzzyChoice

from apps.orders.tests.factories import StoneFactory
from apps.production.enums import ProductionType, QAResult
from apps.production.models import Production


class ProductionFactory(factory.django.DjangoModelFactory):
    """Builds a production step for a new stone."""

    class Meta:
        model = Production

    stone = factory.SubFactory(StoneFactory)
    type = FuzzyChoice(ProductionType.values)
    qa_result = QAResult.PENDING
