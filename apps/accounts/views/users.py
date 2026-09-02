"""User-management views: list, detail, create, edit, activate, delete."""

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView

from apps.core.exceptions import ServiceError
from apps.core.row_actions import action

from ..forms import UserCreateForm, UserUpdateForm
from ..services import create_user, delete_user, set_active, update_user

User = get_user_model()


class UserListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Searchable, filterable, paginated list of users."""

    permission_required = "accounts.view_user"
    template_name = "pages/users/index.html"
    context_object_name = "users"
    paginate_by = 5

    def get_queryset(self):
        qs = User.objects.prefetch_related("groups").order_by("username")
        query = self.request.GET.get("q", "").strip()
        if query:
            cond = (
                Q(username__icontains=query)
                | Q(email__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(groups__name__icontains=query)
            )
            # Let "active" / "inactive" filter by status too (search doubles as filter).
            if query.lower() in ("active", "enabled"):
                cond |= Q(is_active=True)
            elif query.lower() in ("inactive", "disabled"):
                cond |= Q(is_active=False)
            qs = qs.filter(cond).distinct()
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        for user in ctx["users"]:
            user.row_actions = self._actions(user)
        return ctx

    def _actions(self, user):
        acts = [action("View", "lucide:eye", reverse("users:detail", args=[user.pk]))]
        actor = self.request.user
        if actor.has_perm("accounts.change_user"):
            acts.append(
                action("Edit", "lucide:pencil", reverse("users:edit", args=[user.pk]))
            )
            toggle = reverse("users:toggle", args=[user.pk])
            if user.is_active:
                acts.append(
                    action("Deactivate", "lucide:user-x", toggle, method="post")
                )
            else:
                acts.append(
                    action("Activate", "lucide:user-check", toggle, method="post")
                )
        if actor.has_perm("accounts.delete_user"):
            acts.append(
                action(
                    "Delete",
                    "lucide:trash-2",
                    reverse("users:delete", args=[user.pk]),
                    method="post",
                    danger=True,
                )
            )
        return acts


class UserDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """A user's detail page. Uses `user_obj` so it never shadows `request.user`."""

    permission_required = "accounts.view_user"
    template_name = "pages/users/detail.html"
    context_object_name = "user_obj"

    def get_queryset(self):
        return User.objects.prefetch_related("groups")


@login_required
@permission_required("accounts.add_user", raise_exception=True)
def user_create(request):
    """Create a user with an initial password and roles."""
    form = UserCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        cd = form.cleaned_data
        user = create_user(
            username=cd["username"],
            email=cd["email"],
            first_name=cd["first_name"],
            last_name=cd["last_name"],
            password=cd["password1"],
            groups=cd["groups"],
            is_active=cd["is_active"],
        )
        messages.success(request, f"User {user.username} created.")
        return redirect("users:detail", pk=user.pk)
    return render(request, "pages/users/form.html", {"form": form, "mode": "create"})


@login_required
@permission_required("accounts.change_user", raise_exception=True)
def user_edit(request, pk):
    """Edit a user's profile and roles."""
    user = get_object_or_404(User, pk=pk)
    form = UserUpdateForm(request.POST or None, instance=user)
    if request.method == "POST" and form.is_valid():
        cd = form.cleaned_data
        update_user(
            user,
            username=cd["username"],
            email=cd["email"],
            first_name=cd["first_name"],
            last_name=cd["last_name"],
            groups=cd["groups"],
            is_active=cd["is_active"],
        )
        messages.success(request, f"User {user.username} updated.")
        return redirect("users:detail", pk=user.pk)
    return render(
        request,
        "pages/users/form.html",
        {"form": form, "mode": "edit", "user_obj": user},
    )


@login_required
@permission_required("accounts.change_user", raise_exception=True)
@require_POST
def user_toggle_active(request, pk):
    """Activate or deactivate a user."""
    user = get_object_or_404(User, pk=pk)
    try:
        set_active(user, not user.is_active, actor=request.user)
    except ServiceError as exc:
        messages.error(request, str(exc))
    else:
        state = "activated" if user.is_active else "deactivated"
        messages.success(request, f"User {user.username} {state}.")
    return redirect("users:detail", pk=user.pk)


@login_required
@permission_required("accounts.delete_user", raise_exception=True)
@require_POST
def user_delete(request, pk):
    """Permanently delete a user (guarded against self/superuser deletion)."""
    user = get_object_or_404(User, pk=pk)
    try:
        delete_user(user, actor=request.user)
    except ServiceError as exc:
        messages.error(request, str(exc))
        return redirect("users:detail", pk=user.pk)
    messages.success(request, f"User {user.username} deleted.")
    return redirect("users:index")
