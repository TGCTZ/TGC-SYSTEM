"""Permission enforcement helper.

Kept small and dependency-free so any layer can call it. ``perm`` is the full
label, e.g. ``"identification.finalize_report"``.
"""

from django.core.exceptions import PermissionDenied


def require_permission(user, perm: str) -> None:
    """Raise PermissionDenied if the user lacks a permission.

    ``user is None`` means a trusted/system call (webhook, management command)
    and is allowed. Superusers always pass Django's ``has_perm``.
    """
    if user is None:
        return
    if not user.has_perm(perm):
        raise PermissionDenied(f"Missing permission: {perm}")
