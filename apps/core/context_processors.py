"""Template context processors for the core layer."""

import contextlib

from django.conf import settings
from django.urls import NoReverseMatch, reverse

# URL namespace -> (breadcrumb label, index url name) for the section trail.
_SECTIONS = {
    "users": ("Users", "users:index"),
    "manage": ("Manage", "manage:index"),
}


def site(request):
    """Expose ``SITE_NAME`` to every template for app-shell branding."""
    return {"SITE_NAME": settings.SITE_NAME}


def breadcrumbs(request):
    """Build the parent breadcrumb trail (Home → Section) from the current URL.

    The header appends the page title as the final crumb, so this returns only the
    ancestors. Empty on the home page.
    """
    match = getattr(request, "resolver_match", None)
    if match is None or match.view_name == "dashboard:home":
        return {"breadcrumbs": []}

    trail = [{"label": "Home", "url": reverse("dashboard:home")}]
    section = _SECTIONS.get(match.namespace)
    # Skip the section crumb on the section's own index (the title covers it).
    if section and match.url_name != "index":
        with contextlib.suppress(NoReverseMatch):
            trail.append({"label": section[0], "url": reverse(section[1])})
    return {"breadcrumbs": trail}
