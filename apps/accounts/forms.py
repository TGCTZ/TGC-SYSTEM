"""Account forms backing the user-management module."""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from apps.core.forms import StyledFormMixin

User = get_user_model()

_USER_FIELDS = ["username", "email", "first_name", "last_name", "is_active", "groups"]


class UserUpdateForm(StyledFormMixin, forms.ModelForm):
    """Edit a user's profile fields and roles (groups)."""

    class Meta:
        model = User
        fields = _USER_FIELDS


class UserCreateForm(StyledFormMixin, forms.ModelForm):
    """Create a user with an initial password."""

    password1 = forms.CharField(
        label="Password", widget=forms.PasswordInput, strip=False
    )
    password2 = forms.CharField(
        label="Confirm password", widget=forms.PasswordInput, strip=False
    )

    class Meta:
        model = User
        fields = _USER_FIELDS
        field_order = [
            "username",
            "email",
            "first_name",
            "last_name",
            "password1",
            "password2",
            "is_active",
            "groups",
        ]

    def clean_password2(self):
        """Confirm both passwords match and satisfy the validators."""
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("The two password fields don't match.")
        validate_password(password2)
        return password2
