"""Local development settings."""

from .base import *  # noqa: F403

DEBUG = True

# Console email backend — no real mail sent in development.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

INTERNAL_IPS = ["127.0.0.1"]
