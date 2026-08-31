"""Roles & permissions portal: manage Groups, their permissions, and membership."""

from django import forms
from django.apps import apps as django_apps
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Group, Permission
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.core.forms import StyledFormMixin
from apps.core.row_actions import action

User = get_user_model()


def _business_app_labels():
    """App labels for the project's own apps (those under the ``apps.`` package).

    Django built-ins (auth, admin, sessions, …) and third-party apps live outside
    ``apps.``, so filtering on this keeps the matrix focused on business models the
    role actually governs. New apps added under ``apps/`` are included automatically.
    """
    return {
        config.label
        for config in django_apps.get_app_configs()
        if config.name.startswith("apps.")
    }


def _business_permissions():
    """Permissions belonging to business apps, ready for select/order."""
    return Permission.objects.select_related("content_type").filter(
        content_type__app_label__in=_business_app_labels()
    )


def permission_matrix(selected_ids):
    """Group business permissions into apps → models → permissions for the matrix UI.

    Each permission carries its exact database name (e.g. ``Can view stone type``) and
    whether the role grants it. No fixed columns: whatever permissions a model defines
    in the database appear verbatim, ordered by name.
    """
    selected_ids = set(selected_ids)
    perms = _business_permissions().order_by(
        "content_type__app_label", "content_type__model", "name"
    )
    apps: dict = {}
    for perm in perms:
        ct = perm.content_type
        model = apps.setdefault(ct.app_label, {}).setdefault(
            ct.model, {"label": str(ct.name).title(), "perms": []}
        )
        model["perms"].append(
            {
                "perm_id": perm.id,
                "name": perm.name,
                "checked": perm.id in selected_ids,
            }
        )
    return [
        {
            "app_label": app_label,
            "models": [
                {"label": model["label"], "perms": model["perms"]}
                for model in models.values()
            ],
        }
        for app_label, models in apps.items()
    ]


def _selected_ids(request, group):
    """Permission ids to pre-check: from POST on submit, else the role's current set."""
    if request.method == "POST":
        return [int(pk) for pk in request.POST.getlist("permissions")]
    return list(group.permissions.values_list("id", flat=True)) if group else []


def _member_rows(request, group):
    """All users, each flagged whether they belong to the role, for the edit table.

    Selection comes from POST on submit (so an invalid re-render keeps the choices),
    otherwise from the role's current members.
    """
    if request.method == "POST":
        selected = {int(pk) for pk in request.POST.getlist("members")}
    elif group is not None:
        selected = set(group.user_set.values_list("id", flat=True))
    else:
        selected = set()
    users = list(User.objects.order_by("username"))
    for user in users:
        user.in_role = user.id in selected
    return users


def _perm_label(perm):
    """Readable permission label: 'app | model | action'."""
    ct = perm.content_type
    return f"{ct.app_label} | {ct.model} | {perm.name}"


class GroupForm(StyledFormMixin, forms.ModelForm):
    """Create/edit a role (Group) with its permissions and members."""

    permissions = forms.ModelMultipleChoiceField(
        queryset=_business_permissions().order_by(
            "content_type__app_label", "content_type__model", "codename"
        ),
        required=False,
    )
    members = forms.ModelMultipleChoiceField(
        queryset=User.objects.order_by("username"), required=False, label="Users"
    )

    class Meta:
        model = Group
        fields = ["name", "permissions"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["permissions"].label_from_instance = _perm_label
        if self.instance.pk:
            self.fields["members"].initial = self.instance.user_set.all()

    def save(self, commit=True):
        # The matrix only renders business permissions, so a submit omits any
        # infrastructure perms the role holds (e.g. auth.*_group granted to admins).
        # Capture them before save so setting the M2M doesn't silently drop them.
        hidden = (
            list(
                self.instance.permissions.exclude(
                    content_type__app_label__in=_business_app_labels()
                )
            )
            if self.instance.pk
            else []
        )
        group = super().save(commit=commit)
        if commit:
            group.user_set.set(self.cleaned_data["members"])
            if hidden:
                group.permissions.add(*hidden)
        return group


@login_required
@permission_required("auth.view_group", raise_exception=True)
def role_list(request):
    """List roles with member and permission counts."""
    groups = Group.objects.annotate(
        member_count=Count("user", distinct=True),
        perm_count=Count("permissions", distinct=True),
    ).order_by("name")
    for group in groups:
        group.row_actions = _role_actions(request.user, group)
    return render(
        request,
        "pages/manage/roles/index.html",
        {"groups": groups, "can_add": request.user.has_perm("auth.add_group")},
    )


@login_required
@permission_required("auth.view_group", raise_exception=True)
def role_detail(request, pk):
    """Show a role's permissions and members."""
    group = get_object_or_404(Group, pk=pk)
    return render(
        request,
        "pages/manage/roles/detail.html",
        {
            "group": group,
            "users": group.user_set.order_by("username"),
            "matrix": permission_matrix(group.permissions.values_list("id", flat=True)),
            "perm_count": group.permissions.filter(
                content_type__app_label__in=_business_app_labels()
            ).count(),
            "can_change": request.user.has_perm("auth.change_group"),
            "can_delete": request.user.has_perm("auth.delete_group"),
        },
    )


@login_required
@permission_required("auth.add_group", raise_exception=True)
def role_create(request):
    """Create a role."""
    form = GroupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        group = form.save()
        messages.success(request, f"Role {group.name} created.")
        return redirect("manage:role_detail", pk=group.pk)
    return render(
        request,
        "pages/manage/roles/form.html",
        {
            "form": form,
            "mode": "create",
            "matrix": permission_matrix(_selected_ids(request, None)),
            "users": _member_rows(request, None),
        },
    )


@login_required
@permission_required("auth.change_group", raise_exception=True)
def role_edit(request, pk):
    """Edit a role's name, permissions, and members."""
    group = get_object_or_404(Group, pk=pk)
    form = GroupForm(request.POST or None, instance=group)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Role {group.name} updated.")
        return redirect("manage:role_detail", pk=group.pk)
    return render(
        request,
        "pages/manage/roles/form.html",
        {
            "form": form,
            "mode": "edit",
            "group": group,
            "matrix": permission_matrix(_selected_ids(request, group)),
            "users": _member_rows(request, group),
        },
    )


@login_required
@permission_required("auth.delete_group", raise_exception=True)
def role_delete(request, pk):
    """Delete a role."""
    group = get_object_or_404(Group, pk=pk)
    if request.method == "POST":
        name = group.name
        group.delete()
        messages.success(request, f"Role {name} deleted.")
        return redirect("manage:roles")
    return render(request, "pages/manage/roles/delete.html", {"group": group})


def _role_actions(user, group):
    acts = [
        action("View", "lucide:eye", reverse("manage:role_detail", args=[group.pk]))
    ]
    if user.has_perm("auth.change_group"):
        acts.append(
            action(
                "Edit", "lucide:pencil", reverse("manage:role_edit", args=[group.pk])
            )
        )
    if user.has_perm("auth.delete_group"):
        acts.append(
            action(
                "Delete",
                "lucide:trash-2",
                reverse("manage:role_delete", args=[group.pk]),
                danger=True,
            )
        )
    return acts
