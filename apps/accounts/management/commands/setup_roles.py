"""Create the role Groups and assign their permissions from ROLE_PERMISSIONS.

Idempotent: safe to re-run. Assigning users to groups is out of scope (done in
the admin).
"""

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.roles import ROLE_PERMISSIONS


class Command(BaseCommand):
    """Seed role Groups and their permissions."""

    help = "Create/refresh role Groups and their permission assignments."

    @transaction.atomic
    def handle(self, *args, **options):
        for role, perm_labels in ROLE_PERMISSIONS.items():
            group, created = Group.objects.get_or_create(name=role)
            perms = [self._resolve(label) for label in perm_labels]
            group.permissions.set(perms)
            verb = "Created" if created else "Updated"
            self.stdout.write(
                self.style.SUCCESS(f"{verb} '{role}' with {len(perms)} permission(s).")
            )

    def _resolve(self, label: str) -> Permission:
        """Turn 'app_label.codename' into a Permission, or fail loudly."""
        app_label, codename = label.split(".", 1)
        try:
            return Permission.objects.get(
                content_type__app_label=app_label, codename=codename
            )
        except Permission.DoesNotExist as exc:
            raise ValueError(f"Unknown permission: {label}") from exc
