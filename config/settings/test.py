"""Test settings — optimized for speed."""

from .base import *  # noqa: F403

DEBUG = False

# Fast, insecure password hasher — acceptable in tests only.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# In-memory cache; no external services during tests.
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
