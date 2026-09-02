"""Admin-panel views: dashboard, generic model CRUD, and the activity feed."""

from datetime import timedelta

from auditlog.models import LogEntry

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.exceptions import FieldDoesNotExist, PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from apps.core.row_actions import action

from .registry import site

User = get_user_model()

_ACTION_VERBS = {
    LogEntry.Action.CREATE: "created",
    LogEntry.Action.UPDATE: "updated",
    LogEntry.Action.DELETE: "deleted",
}


# --- helpers ---------------------------------------------------------------
def _panel_or_404(app_label, model_name):
    panel = site.get(app_label, model_name)
    if panel is None:
        raise Http404("Model is not registered with the admin panel.")
    return panel


def _require(user, panel, act):
    if not user.has_perm(panel.perm(act)):
        raise PermissionDenied


def _staff_only(user):
    if not user.is_staff:
        raise PermissionDenied


def _has_field(panel, name):
    try:
        panel.opts.get_field(name)
        return True
    except FieldDoesNotExist:
        return False


def _render_cell(obj, name):
    """Render a value for a list/detail cell as {kind, value}."""
    getter = getattr(obj, f"get_{name}_display", None)
    value = getter() if callable(getter) else getattr(obj, name, None)
    if callable(value):
        value = value()
    if isinstance(value, bool):
        return {"kind": "bool", "value": value}
    if value in (None, ""):
        return {"kind": "text", "value": "—"}
    return {"kind": "text", "value": str(value)}


def _column_header(panel, name, current_sort):
    orderable = _has_field(panel, name)
    if orderable:
        label = str(panel.opts.get_field(name).verbose_name).title()
    else:
        label = name.replace("_", " ").title()
    header = {"name": name, "label": label, "orderable": orderable}
    if orderable:
        header["next"] = f"-{name}" if current_sort == name else name
        header["indicator"] = {name: "↑", f"-{name}": "↓"}.get(current_sort, "")
    return header


def _row_actions(user, panel, obj):
    args = [panel.app_label, panel.model_name, obj.pk]
    acts = [action("View", "lucide:eye", reverse("backoffice:detail", args=args))]
    if user.has_perm(panel.perm("change")):
        acts.append(
            action("Edit", "lucide:pencil", reverse("backoffice:edit", args=args))
        )
    if user.has_perm(panel.perm("delete")):
        acts.append(
            action(
                "Delete",
                "lucide:trash-2",
                reverse("backoffice:delete", args=args),
                danger=True,
            )
        )
    return acts


def _filter_options(panel, request):
    filters = []
    for name in panel.list_filter:
        field = panel.opts.get_field(name)
        if field.choices:
            options = [(str(v), label) for v, label in field.choices]
        elif field.get_internal_type() == "BooleanField":
            options = [("true", "Yes"), ("false", "No")]
        else:
            continue
        filters.append(
            {
                "name": name,
                "label": str(field.verbose_name).title(),
                "options": options,
                "current": request.GET.get(name, ""),
            }
        )
    return filters


def _activity_row(entry):
    return {
        "actor": entry.actor,
        "verb": _ACTION_VERBS.get(entry.action, "changed"),
        "model": entry.content_type.model if entry.content_type else "record",
        "repr": entry.object_repr,
        "timestamp": entry.timestamp,
    }


# --- dashboard & activity --------------------------------------------------
@login_required
def index(request):
    """Admin dashboard: KPI stats, a card per registered model, and recent activity."""
    _staff_only(request.user)
    panels = [p for p in site.all() if request.user.has_perm(p.perm("view"))]
    week_ago = timezone.now() - timedelta(days=7)

    stats = [
        {"label": "Users", "value": User.objects.count(), "icon": "lucide:users"},
        {
            "label": "Active users",
            "value": User.objects.filter(is_active=True).count(),
            "icon": "lucide:user-check",
        },
        {"label": "Roles", "value": Group.objects.count(), "icon": "lucide:shield"},
    ]

    cards = []
    for panel in panels:
        qs = panel.get_queryset()
        delta = (
            qs.filter(created_at__gte=week_ago).count()
            if _has_field(panel, "created_at")
            else None
        )
        cards.append(
            {
                "panel": panel,
                "count": qs.count(),
                "delta": delta,
                "url": reverse(
                    "backoffice:list", args=[panel.app_label, panel.model_name]
                ),
            }
        )

    recent = [
        _activity_row(e)
        for e in LogEntry.objects.select_related("actor", "content_type").order_by(
            "-timestamp"
        )[:8]
    ]
    return render(
        request,
        "pages/backoffice/index.html",
        {"stats": stats, "cards": cards, "recent": recent},
    )


@login_required
def activity(request):
    """Paginated global activity feed from the audit log."""
    _staff_only(request.user)
    qs = LogEntry.objects.select_related("actor", "content_type").order_by("-timestamp")
    page = Paginator(qs, 25).get_page(request.GET.get("page"))
    rows = [_activity_row(e) for e in page]
    return render(
        request, "pages/backoffice/activity.html", {"rows": rows, "page_obj": page}
    )


# --- generic model CRUD ----------------------------------------------------
@login_required
def object_list(request, app_label, model_name):
    """Searchable, filterable, sortable, paginated list for a registered model."""
    panel = _panel_or_404(app_label, model_name)
    _require(request.user, panel, "view")
    qs = panel.get_queryset()

    query = request.GET.get("q", "").strip()
    if query and panel.search_fields:
        cond = Q()
        for field in panel.search_fields:
            cond |= Q(**{f"{field}__icontains": query})
        qs = qs.filter(cond)

    for name in panel.list_filter:
        val = request.GET.get(name)
        if not val:
            continue
        if panel.opts.get_field(name).get_internal_type() == "BooleanField":
            qs = qs.filter(**{name: val == "true"})
        else:
            qs = qs.filter(**{name: val})

    columns = panel.get_list_display()
    sort = request.GET.get("sort", "")
    if sort and sort.lstrip("-") in columns and _has_field(panel, sort.lstrip("-")):
        qs = qs.order_by(sort)
    elif panel.ordering:
        qs = qs.order_by(*panel.ordering)

    page = Paginator(qs, panel.list_per_page).get_page(request.GET.get("page"))
    rows = [
        {
            "obj": obj,
            "cells": [_render_cell(obj, c) for c in columns],
            "actions": _row_actions(request.user, panel, obj),
        }
        for obj in page
    ]
    return render(
        request,
        "pages/backoffice/list.html",
        {
            "panel": panel,
            "columns": [_column_header(panel, c, sort) for c in columns],
            "rows": rows,
            "page_obj": page,
            "query": query,
            "filters": _filter_options(panel, request),
            "can_add": panel.can_create and request.user.has_perm(panel.perm("add")),
        },
    )


@login_required
def object_detail(request, app_label, model_name, pk):
    """Read-only detail for one record."""
    panel = _panel_or_404(app_label, model_name)
    _require(request.user, panel, "view")
    obj = get_object_or_404(panel.get_queryset(), pk=pk)
    fields = [
        {"label": name.replace("_", " ").title(), "cell": _render_cell(obj, name)}
        for name in panel.get_form_fields()
    ]
    return render(
        request,
        "pages/backoffice/detail.html",
        {
            "panel": panel,
            "object": obj,
            "fields": fields,
            "can_change": request.user.has_perm(panel.perm("change")),
            "can_delete": request.user.has_perm(panel.perm("delete")),
        },
    )


@login_required
def object_create(request, app_label, model_name):
    """Create a record via the auto-generated form."""
    panel = _panel_or_404(app_label, model_name)
    _require(request.user, panel, "add")
    if not panel.can_create:
        raise Http404("This model can't be created from the panel.")
    form = panel.get_form_class()(request.POST or None)
    if request.method == "POST" and form.is_valid():
        obj = form.save()
        messages.success(request, f"{panel.verbose_name} created.")
        return redirect("backoffice:detail", app_label, model_name, obj.pk)
    return render(
        request,
        "pages/backoffice/form.html",
        {"panel": panel, "form": form, "mode": "create"},
    )


@login_required
def object_edit(request, app_label, model_name, pk):
    """Edit a record via the auto-generated form."""
    panel = _panel_or_404(app_label, model_name)
    _require(request.user, panel, "change")
    obj = get_object_or_404(panel.get_queryset(), pk=pk)
    form = panel.get_form_class()(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"{panel.verbose_name} updated.")
        return redirect("backoffice:detail", app_label, model_name, obj.pk)
    return render(
        request,
        "pages/backoffice/form.html",
        {"panel": panel, "form": form, "mode": "edit", "object": obj},
    )


@login_required
def object_delete(request, app_label, model_name, pk):
    """Confirm and delete a record (soft delete when the model supports it)."""
    panel = _panel_or_404(app_label, model_name)
    _require(request.user, panel, "delete")
    obj = get_object_or_404(panel.get_queryset(), pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, f"{panel.verbose_name} deleted.")
        return redirect("backoffice:list", app_label, model_name)
    return render(
        request, "pages/backoffice/delete.html", {"panel": panel, "object": obj}
    )
