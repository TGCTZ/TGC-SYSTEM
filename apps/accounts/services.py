"""Service layer for user management. Views call these; rules live here.

The current user is stamped on audited models by the current-user middleware; these
services take an explicit ``actor`` only where a rule depends on who is acting
(e.g. you can't deactivate or delete yourself).
"""

from django.contrib.auth import get_user_model

from apps.core.exceptions import ServiceError

User = get_user_model()


def create_user(
    *, username, email, first_name, last_name, password, groups, is_active=True
):
    """Create a user, set their password, and assign groups (roles)."""
    user = User(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        is_active=is_active,
    )
    user.set_password(password)
    user.save()
    user.groups.set(groups)
    return user


def update_user(user, *, username, email, first_name, last_name, groups, is_active):
    """Update a user's profile fields and group membership."""
    user.username = username
    user.email = email
    user.first_name = first_name
    user.last_name = last_name
    user.is_active = is_active
    user.save()
    user.groups.set(groups)
    return user


def set_active(user, active, *, actor):
    """Activate or deactivate a user, protecting against self-lockout."""
    if not active:
        if user == actor:
            raise ServiceError("You can't deactivate your own account.")
        if user.is_superuser and _active_superuser_count() <= 1:
            raise ServiceError("You can't deactivate the last active superuser.")
    user.is_active = active
    user.save(update_fields=["is_active"])
    return user


def delete_user(user, *, actor):
    """Permanently delete a user, protecting yourself and superusers."""
    if user == actor:
        raise ServiceError("You can't delete your own account.")
    if user.is_superuser:
        raise ServiceError("Superusers can't be deleted from here (use the admin).")
    user.delete()


def _active_superuser_count():
    """Number of active superusers — used to prevent locking everyone out."""
    return User.objects.filter(is_superuser=True, is_active=True).count()
