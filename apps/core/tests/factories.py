"""Factories for core reference data and pricing."""

import factory
from factory.fuzzy import FuzzyChoice

from apps.core.enums import ColorGroup, StoneCategory
from apps.core.models import (
    Color,
    Instrument,
    Origin,
    ShapeCut,
    Species,
    StonePrice,
    StoneType,
    Variety,
)


class StoneTypeFactory(factory.django.DjangoModelFactory):
    """Builds a stone type."""

    class Meta:
        model = StoneType
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Stone Type {n}")
    category = FuzzyChoice(StoneCategory.values)


class SpeciesFactory(factory.django.DjangoModelFactory):
    """Builds a species."""

    class Meta:
        model = Species
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Species {n}")


class VarietyFactory(factory.django.DjangoModelFactory):
    """Builds a variety under a species."""

    class Meta:
        model = Variety
        django_get_or_create = ("name", "species")

    name = factory.Sequence(lambda n: f"Variety {n}")
    species = factory.SubFactory(SpeciesFactory)


class ColorFactory(factory.django.DjangoModelFactory):
    """Builds a color filed under a color family."""

    class Meta:
        model = Color
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Color {n}")
    group = FuzzyChoice(ColorGroup.values)


class OriginFactory(factory.django.DjangoModelFactory):
    """Builds an origin."""

    class Meta:
        model = Origin
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Origin {n}")


class ShapeCutFactory(factory.django.DjangoModelFactory):
    """Builds a shape/cut."""

    class Meta:
        model = ShapeCut
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Shape {n}")


class InstrumentFactory(factory.django.DjangoModelFactory):
    """Builds an instrument."""

    class Meta:
        model = Instrument
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Instrument {n}")


class StonePriceFactory(factory.django.DjangoModelFactory):
    """Builds the fixed price for a stone type."""

    class Meta:
        model = StonePrice
        django_get_or_create = ("stone_type",)

    stone_type = factory.SubFactory(StoneTypeFactory)
    price = 10_000
