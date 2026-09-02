"""Identification forms.

The workflow has two phases: first the gemmologist assigns the stone's *type* (which
fixes the price), the customer pays, then the gemmologist records the *findings*.
"""

from decimal import Decimal

from django import forms

from apps.core.enums import WeightUnit
from apps.core.forms import StyledFormMixin
from apps.core.models import (
    Color,
    Instrument,
    Origin,
    ShapeCut,
    Species,
    StoneType,
    Variety,
)

from .enums import NatureType, OpticCharacter, Transparency, Treatment


def _optional_choices(choices):
    """Prepend a blank "—" entry so a choice field can be left unset."""
    return [("", "—"), *choices]


class _GroupedModelChoiceIterator(forms.models.ModelChoiceIterator):
    """Yields the blank option, then one ``<optgroup>`` per group value.

    Groups appear in the declaration order of the grouping field's own choices;
    rows within a group keep the queryset's ordering.
    """

    def __iter__(self):
        """Emit the blank choice, then ``(group_label, [choices])`` tuples."""
        if self.field.empty_label is not None:
            yield ("", self.field.empty_label)
        group_field = self.queryset.model._meta.get_field(self.field.group_by)
        labels = dict(group_field.flatchoices)
        buckets = {}
        for obj in self.queryset:
            buckets.setdefault(getattr(obj, self.field.group_by), []).append(obj)
        for value, label in labels.items():
            rows = buckets.get(value)
            if rows:
                yield label, [self.choice(obj) for obj in rows]


class GroupedModelChoiceField(forms.ModelChoiceField):
    """A ``ModelChoiceField`` rendered as ``<optgroup>``s keyed by ``group_by``."""

    iterator = _GroupedModelChoiceIterator

    def __init__(self, *args, group_by, **kwargs):
        self.group_by = group_by
        super().__init__(*args, **kwargs)


class StoneTypeForm(StyledFormMixin, forms.Form):
    """Phase 1 — register a stone under its priced type (no findings yet)."""

    stone_type = forms.ModelChoiceField(
        queryset=StoneType.objects.filter(is_active=True), label="Stone type"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only three fixed types — a plain select is clearer (and never clipped) than
        # a searchable Tom Select combobox.
        self.fields["stone_type"].widget.attrs.pop("data-search", None)


class FindingsForm(StyledFormMixin, forms.Form):
    """Phase 2 — record weight and the gemmological findings (after payment)."""

    weight = forms.DecimalField(
        max_digits=10, decimal_places=3, min_value=Decimal("0.001")
    )
    weight_unit = forms.ChoiceField(
        choices=WeightUnit.choices, initial=WeightUnit.CARAT
    )

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
        queryset=ShapeCut.objects.filter(is_active=True),
        required=False,
        label="Shape / cut",
    )
    color = GroupedModelChoiceField(
        queryset=Color.objects.filter(is_active=True).order_by("name"),
        group_by="group",
        required=False,
        empty_label="—",
    )
    nature_type = forms.ChoiceField(
        choices=_optional_choices(NatureType.choices), required=False, label="Nature"
    )
    transparency = forms.ChoiceField(
        choices=_optional_choices(Transparency.choices), required=False
    )
    treatment = forms.ChoiceField(
        choices=_optional_choices(Treatment.choices), required=False
    )
    optic_character = forms.ChoiceField(
        choices=_optional_choices(OpticCharacter.choices), required=False
    )
    dimensions = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "e.g. 6.5 x 4.8 x 3.2 mm"}),
        help_text="Length x Width x Depth",
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
