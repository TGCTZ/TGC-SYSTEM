"""Local development settings."""

from .base import *

DEBUG = True

# Console email backend — no real mail sent in development.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

INTERNAL_IPS = ["127.0.0.1"]

# Skip the real GePG bill submission in dev — return an instant control number.
GEPG_SIMULATE = config("GEPG_SIMULATE", default=True, cast=bool)
