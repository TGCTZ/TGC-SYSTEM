"""Admin-managed reference (lookup) tables."""

from django.db import models
from django.db.models import Q

from apps.core.enums import ColorGroup, StoneCategory

from .reference import ReferenceModel


class StoneType(ReferenceModel):
    """A type of stone (e.g. ruby, sapphire); its category drives pricing."""

    category = models.CharField(max_length=20, choices=StoneCategory.choices)


class Species(ReferenceModel):
    """Gemmological species."""

    class Meta(ReferenceModel.Meta):
        verbose_name_plural = "species"


class Variety(ReferenceModel):
    """A variety within a species."""

    species = models.ForeignKey(
        Species, on_delete=models.PROTECT, related_name="varieties"
    )

    class Meta(ReferenceModel.Meta):
        verbose_name_plural = "varieties"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "species"],
                condition=Q(deleted_at__isnull=True),
                name="%(app_label)s_%(class)s_unique_name_species",
            ),
        ]


class Color(ReferenceModel):
    """Observed stone color, filed under a broad color family."""

    group = models.CharField(max_length=20, choices=ColorGroup.choices)


class Origin(ReferenceModel):
    """Geographic origin of a stone."""


class ShapeCut(ReferenceModel):
    """Shape or cut of a stone."""


class Instrument(ReferenceModel):
    """Lab instrument used during identification."""
