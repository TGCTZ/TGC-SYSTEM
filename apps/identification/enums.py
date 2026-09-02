"""Enums owned by identification: fixed gemmological attribute values."""

from django.db import models


class Transparency(models.TextChoices):
    """How light passes through the stone."""

    TRANSPARENT = ("transparent", "Transparent")
    TRANSLUCENT = ("translucent", "Translucent")
    OPAQUE = ("opaque", "Opaque")


class NatureType(models.TextChoices):
    """Whether the stone is natural or man-made/altered."""

    NATURAL = ("natural", "Natural")
    SYNTHETIC = ("synthetic", "Synthetic")
    TREATED = ("treated", "Treated")
    ENHANCED = ("enhanced", "Enhanced")
    ARTIFICIAL = ("artificial", "Artificial")


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

    SR = ("sr", "SR — Singly refractive")
    ADR = ("adr", "ADR — Anomalous double refractive")
    DR = ("dr", "DR — Double refractive")
    AGG = ("agg", "AGG — Aggregate")
