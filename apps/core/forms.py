"""Shared form styling: apply Tailwind classes to widgets for cotton rendering."""

from django import forms

# shadcn input/select styling on the design tokens (mirrors the cotton form atoms).
CONTROL_CLASSES = (
    "flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm "
    "text-foreground shadow-xs transition-colors placeholder:text-muted-foreground "
    "focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 "
    "focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50"
)
# Textareas grow with `rows`, so no fixed height.
TEXTAREA_CLASSES = CONTROL_CLASSES.replace("flex h-9 ", "flex min-h-16 ").replace(
    "px-3 py-1 ", "px-3 py-2 "
)
CHECKBOX_CLASSES = (
    "h-4 w-4 rounded border-input accent-primary "
    "focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-none"
)


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
                widget.attrs.setdefault("class", TEXTAREA_CLASSES)
                widget.attrs.setdefault("rows", 3)
            else:
                widget.attrs.setdefault("class", CONTROL_CLASSES)
