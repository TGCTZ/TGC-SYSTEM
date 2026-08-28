"""Enums owned by identification: fixed gemmological attribute values."""

from django.db import models


class Color(models.TextChoices):
    """Observed stone color."""

    COLORLESS = ("colorless", "Colorless")
    WHITE = ("white", "White")
    RED = ("red", "Red")
    PINK = ("pink", "Pink")
    ORANGE = ("orange", "Orange")
    YELLOW = ("yellow", "Yellow")
    GREEN = ("green", "Green")
    BLUE = ("blue", "Blue")
    VIOLET = ("violet", "Violet")
    PURPLE = ("purple", "Purple")
    BROWN = ("brown", "Brown")
    BLACK = ("black", "Black")
    GRAY = ("gray", "Gray")
    MULTICOLOR = ("multicolor", "Multicolor")


class Transparency(models.TextChoices):
    """How light passes through the stone."""

    TRANSPARENT = ("transparent", "Transparent")
    SEMI_TRANSPARENT = ("semi_transparent", "Semi-transparent")
    TRANSLUCENT = ("translucent", "Translucent")
    OPAQUE = ("opaque", "Opaque")


class Treatment(models.TextChoices):
    """Enhancement applied to the stone, if any."""

    NONE = ("none", "None")
    HEATED = ("heated", "Heated")
    OILED = ("oiled", "Oiled")
    DYED = ("dyed", "Dyed")
    IRRADIATED = ("irradiated", "Irradiated")
    FRACTURE_FILLED = ("fracture_filled", "Fracture filled")
    BLEACHED = ("bleached", "Bleached")
    IMPREGNATED = ("impregnated", "Impregnated")


class OpticCharacter(models.TextChoices):
    """Optical behavior under polarized light."""

    ISOTROPIC = ("isotropic", "Isotropic")
    UNIAXIAL_POSITIVE = ("uniaxial_positive", "Uniaxial (+)")
    UNIAXIAL_NEGATIVE = ("uniaxial_negative", "Uniaxial (−)")
    BIAXIAL_POSITIVE = ("biaxial_positive", "Biaxial (+)")
    BIAXIAL_NEGATIVE = ("biaxial_negative", "Biaxial (−)")
    AGGREGATE = ("aggregate", "Aggregate")
