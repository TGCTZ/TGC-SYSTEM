"""Identification forms."""

from decimal import Decimal

from django import forms

from apps.core.enums import WeightUnit
from apps.core.forms import StyledFormMixin
from apps.core.models import Instrument, Origin, ShapeCut, Species, StoneType, Variety

from .enums import Color, OpticCharacter, Transparency, Treatment


def _optional_choices(choices):
    return [("", "—"), *choices]


class StoneIdentificationForm(StyledFormMixin, forms.Form):
    """Register a stone and record its identification findings."""

    # Stone (recorded at identification)
    stone_type = forms.ModelChoiceField(queryset=StoneType.objects.filter(is_active=True))
    weight = forms.DecimalField(max_digits=10, decimal_places=3, min_value=Decimal("0.001"))
    weight_unit = forms.ChoiceField(choices=WeightUnit.choices, initial=WeightUnit.CARAT)

    # Findings
    species = forms.ModelChoiceField(
        queryset=Species.objects.filter(is_active=True), required=False
    )
    variety = forms.ModelChoiceField(
        queryset=Variety.objects.filter(is_active=True), required=False
    )
    origin = forms.ModelChoiceField(
        queryset=Origin.objects.filter(is_active=True), required=False
    )
    shape_cut = forms.ModelChoiceField(
        queryset=ShapeCut.objects.filter(is_active=True), required=False, label="Shape / cut"
    )
    color = forms.ChoiceField(choices=_optional_choices(Color.choices), required=False)
    transparency = forms.ChoiceField(
        choices=_optional_choices(Transparency.choices), required=False
    )
    treatment = forms.ChoiceField(
        choices=_optional_choices(Treatment.choices), required=False
    )
    optic_character = forms.ChoiceField(
        choices=_optional_choices(OpticCharacter.choices), required=False
    )
    refractive_index = forms.CharField(max_length=50, required=False)
    specific_gravity = forms.DecimalField(
        max_digits=10, decimal_places=3, required=False
    )
    is_polished = forms.BooleanField(required=False, label="Polished")
    instruments = forms.ModelMultipleChoiceField(
        queryset=Instrument.objects.filter(is_active=True),
        required=False,
        label="Instruments used",
    )
    conclusion = forms.CharField(widget=forms.Textarea, required=False)
