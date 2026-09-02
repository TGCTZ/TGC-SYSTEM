"""Factories for identification."""

import factory
from factory.fuzzy import FuzzyChoice

from apps.core.tests.factories import ColorFactory, InstrumentFactory, SpeciesFactory
from apps.identification.enums import Transparency
from apps.identification.models import IdentificationReport, InstrumentUsed
from apps.orders.tests.factories import StoneFactory


class IdentificationReportFactory(factory.django.DjangoModelFactory):
    """Builds a report for a new stone."""

    class Meta:
        model = IdentificationReport

    stone = factory.SubFactory(StoneFactory)
    report_number = factory.Sequence(lambda n: f"RPT-{n:05d}")
    species = factory.SubFactory(SpeciesFactory)
    color = factory.SubFactory(ColorFactory)
    transparency = FuzzyChoice(Transparency.values)


class InstrumentUsedFactory(factory.django.DjangoModelFactory):
    """Builds an instrument-used row on a new report."""

    class Meta:
        model = InstrumentUsed

    report = factory.SubFactory(IdentificationReportFactory)
    instrument = factory.SubFactory(InstrumentFactory)
    reading = factory.Faker("numerify", text="#.###")
