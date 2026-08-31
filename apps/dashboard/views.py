"""Dashboard and component-styleguide views."""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.utils import timezone
from django.views.generic import TemplateView

from apps.core.row_actions import action


class HomeView(LoginRequiredMixin, TemplateView):
    """Authenticated landing page."""

    template_name = "pages/dashboard/home.html"


class StyleguideView(TemplateView):
    """Gallery of UI components for development and preview."""

    template_name = "pages/styleguide.html"

    # Maps ?toast=<key> to a (messages function, demo text) pair so each toast
    # variant can be triggered on demand from the styleguide.
    _TOASTS = {
        "info": (messages.info, "An informational message."),
        "success": (messages.success, "The order was created."),
        "warning": (messages.warning, "Price is missing for a stone type."),
        "error": (messages.error, "The bill could not be submitted."),
    }

    def get(self, request, *args, **kwargs):
        """Fire a demo toast when ?toast=<variant> is present, then render."""
        add_message, text = self._TOASTS.get(request.GET.get("toast"), (None, None))
        if add_message:
            add_message(request, text)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["table_headers"] = ["Reference", "Customer", "Status"]
        # Few actions render inline as icons; many collapse to 3 + an overflow menu.
        ctx["few_actions"] = [
            action("View", "lucide:eye", "#"),
            action("Edit", "lucide:pencil", "#"),
        ]
        ctx["many_actions"] = [
            action("View", "lucide:eye", "#"),
            action("Edit", "lucide:pencil", "#"),
            action("Duplicate", "lucide:copy", "#"),
            action("Archive", "lucide:archive", "#"),
            action("Delete", "lucide:trash-2", "#", danger=True),
        ]
        # A throwaway paginator gives the pagination component a real page_obj.
        ctx["page_obj"] = Paginator(list(range(25)), 5).page(2)
        return ctx


def htmx_demo(request):
    """Return a small partial to demonstrate an HTMX swap."""
    now = timezone.now().strftime("%H:%M:%S")
    return HttpResponse(
        f'<div class="rounded-md bg-green-100 px-3 py-2 text-sm text-green-800">'
        f"Swapped in by HTMX at {now}.</div>"
    )
