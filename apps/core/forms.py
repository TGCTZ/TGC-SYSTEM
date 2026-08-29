"""Shared form styling: apply Tailwind classes to widgets for cotton rendering."""

from django import forms

CONTROL_CLASSES = (
    "block w-full rounded-md border-0 px-3 py-1.5 text-sm text-gray-900 shadow-sm "
    "ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 "
    "focus:ring-2 focus:ring-inset focus:ring-blue-600"
)
CHECKBOX_CLASSES = "h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"


class StyledFormMixin:
    """Style every widget with our classes; make selects searchable (Tom Select)."""

    error_css_class = "has-error"
    required_css_class = "is-required"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", CHECKBOX_CLASSES)
            elif isinstance(widget, forms.Select):  # covers SelectMultiple
                widget.attrs.setdefault("class", CONTROL_CLASSES)
                widget.attrs.setdefault("data-search", "")
            elif isinstance(widget, forms.Textarea):
                widget.attrs.setdefault("class", CONTROL_CLASSES)
                widget.attrs.setdefault("rows", 3)
            else:
                widget.attrs.setdefault("class", CONTROL_CLASSES)
