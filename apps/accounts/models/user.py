"""Custom user model.

Defined on day one (before the first migration) so AUTH_USER_MODEL can never
be swapped later — a change Django makes extremely painful. It currently mirrors
Django's default user by extending AbstractUser; add profile fields, roles, and
methods here as the domain requires.
"""

from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Application user. Extend with domain-specific fields as needed."""

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
