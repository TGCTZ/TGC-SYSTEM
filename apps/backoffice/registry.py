"""Registry of ModelPanels — the framework's catalog of managed models.

Apps register their models in ``<app>/panels.py``:

    from apps.backoffice.registry import site
    site.register(MyModel, MyModelPanel)
"""


class AlreadyRegisteredError(Exception):
    """Raised when a model is registered twice."""


class Registry:
    """Maps (app_label, model_name) to a ModelPanel instance."""

    def __init__(self):
        self._panels = {}

    def register(self, model, panel_class=None):
        """Register ``model`` with an optional ModelPanel subclass."""
        from .panels import ModelPanel

        panel_class = panel_class or ModelPanel
        key = (model._meta.app_label, model._meta.model_name)
        if key in self._panels:
            raise AlreadyRegisteredError(f"{key[0]}.{key[1]} is already registered")
        self._panels[key] = panel_class(model)

    def get(self, app_label, model_name):
        """Return the panel for a model, or ``None`` if not registered."""
        return self._panels.get((app_label, model_name))

    def all(self):
        """All registered panels, sorted by label."""
        return sorted(self._panels.values(), key=lambda p: p.verbose_name_plural)


site = Registry()
