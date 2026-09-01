"""ModelPanel — declarative config for a model's admin screens (like ModelAdmin).

Subclass and set the class attributes, then register with the panel site:

    class StoneTypePanel(ModelPanel):
        list_display = ("name", "category", "is_active")
        list_filter = ("category", "is_active")
        search_fields = ("name",)
"""

from django import forms
from django.forms import modelform_factory

from apps.core.forms import StyledFormMixin
from apps.core.models import BaseModel

# Never shown in generated list columns or forms.
AUDIT_FIELDS = {
    "created_at",
    "created_by",
    "updated_at",
    "updated_by",
    "deleted_at",
    "deleted_by",
}


class _StyledModelForm(StyledFormMixin, forms.ModelForm):
    """Base for auto-generated forms so every widget gets styled."""


class ModelPanel:
    """How a model is presented and edited in the admin panel."""

    list_display: tuple | None = None  # field/method names; None → auto
    list_filter: tuple = ()  # fields with choices or boolean → filter dropdowns
    search_fields: tuple = ()  # icontains-OR search
    ordering: tuple | None = None  # default ordering, e.g. ("-created_at",)
    list_per_page: int = 5
    form_fields: tuple | None = None  # None → editable non-audit fields
    can_create: bool = True  # False if required fields aren't user-editable
    label: str | None = None  # overrides the singular display name
    icon: str = "lucide:database"

    def __init__(self, model):
        self.model = model
        self.opts = model._meta

    @property
    def app_label(self):
        """The model's app label."""
        return self.opts.app_label

    @property
    def model_name(self):
        """The model's lowercase name."""
        return self.opts.model_name

    @property
    def verbose_name(self):
        """Singular display name."""
        return self.label or str(self.opts.verbose_name).title()

    @property
    def verbose_name_plural(self):
        """Plural display name."""
        return str(self.opts.verbose_name_plural).title()

    @property
    def is_soft_delete(self):
        """True if the model uses BaseModel soft delete."""
        return issubclass(self.model, BaseModel)

    def perm(self, action):
        """Permission label for an action, e.g. ``app.change_model``."""
        return f"{self.app_label}.{action}_{self.model_name}"

    def get_queryset(self):
        """Base queryset for the list screen."""
        return self.model._default_manager.all()

    def get_list_display(self):
        """Column names for the list screen."""
        if self.list_display:
            return list(self.list_display)
        names = [
            f.name
            for f in self.opts.concrete_fields
            if not f.primary_key and f.name not in AUDIT_FIELDS
        ]
        return names[:5] or ["pk"]

    def get_form_fields(self):
        """Editable field names for the create/edit form."""
        if self.form_fields:
            return list(self.form_fields)
        return [
            f.name
            for f in self.opts.concrete_fields
            if f.editable and not f.primary_key and f.name not in AUDIT_FIELDS
        ]

    def get_form_class(self):
        """A styled ModelForm for this model."""
        return modelform_factory(
            self.model, form=_StyledModelForm, fields=self.get_form_fields()
        )
