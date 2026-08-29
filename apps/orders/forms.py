"""Reception forms."""

from django import forms

from apps.core.forms import StyledFormMixin


class OrderCreateForm(StyledFormMixin, forms.Form):
    """Register a customer and how many stones they submitted."""

    first_name = forms.CharField(max_length=100)
    middle_name = forms.CharField(max_length=100, required=False)
    last_name = forms.CharField(max_length=100)
    phone = forms.CharField(max_length=20)
    email = forms.EmailField(required=False)
    region = forms.CharField(max_length=100, required=False)
    stone_count = forms.IntegerField(
        min_value=1,
        label="Number of stones",
        help_text="How many stones the customer submitted. Their properties are "
        "recorded later, during identification.",
    )
