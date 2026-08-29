"""Dashboard and component-styleguide views."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.utils import timezone
from django.views.generic import TemplateView


class HomeView(LoginRequiredMixin, TemplateView):
    """Authenticated landing page."""

    template_name = "pages/dashboard/home.html"


class StyleguideView(TemplateView):
    """Gallery of UI components for development and preview."""

    template_name = "pages/styleguide.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["table_headers"] = ["Reference", "Customer", "Status", ""]
        return ctx


def htmx_demo(request):
    """Return a small partial to demonstrate an HTMX swap."""
    now = timezone.now().strftime("%H:%M:%S")
    return HttpResponse(
        f'<div class="rounded-md bg-green-100 px-3 py-2 text-sm text-green-800">'
        f"Swapped in by HTMX at {now}.</div>"
    )
