"""Helpers for building per-row action lists for the row-actions component.

Views build a list of these dicts per row (permission-filtered) and pass it to
``<c-atoms.ui.row-actions :actions="obj.row_actions" />``. Centralising the dict
shape here keeps every call site consistent.
"""


def action(label, icon, url, *, method="get", danger=False):
    """Build one row-action dict.

    Args:
        label: Human label (shown in the menu, used as the icon tooltip).
        icon: Iconify name, e.g. ``lucide:eye``.
        url: Target URL (usually from ``reverse()``).
        method: ``"get"`` renders a link; ``"post"`` renders a CSRF-protected form.
        danger: Style the action as destructive (red).

    Returns:
        A dict consumed by the ``row-actions`` / ``action-icon`` components.
    """
    return {
        "label": label,
        "icon": icon,
        "url": url,
        "method": method,
        "danger": danger,
    }
