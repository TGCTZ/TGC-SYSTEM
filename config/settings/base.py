"""
Base settings shared across all environments.

Environment-specific modules (development, production, test) import everything
from here and override as needed. Selected via DJANGO_SETTINGS_MODULE.

Secrets and environment-specific values come from environment variables
(see .env.example). Nothing sensitive is hard-coded here.
"""

from pathlib import Path

from decouple import Csv, config

# BASE_DIR points at the repository root (three levels up from this file:
# config/settings/base.py -> config/settings -> config -> <root>).
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# ------------------------------------------------------------
# Core
# ------------------------------------------------------------
SECRET_KEY = config("SECRET_KEY")  # no default — must be set, fail loud
DEBUG = config("DEBUG", default=False, cast=bool)  # safe default: off
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="127.0.0.1,localhost", cast=Csv())

# Display name for app-shell branding (header, breadcrumbs). See core.context_processors.
SITE_NAME = config("SITE_NAME", default="TGC System")


# ------------------------------------------------------------
# Applications
# ------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
]

THIRD_PARTY_APPS: list[str] = [
    "auditlog",
    "django_cotton",
    "dj_iconify",
]

# Local apps, ordered by dependency layer (low -> high). See docs/conventions.md.
LOCAL_APPS = [
    "apps.core",       # L1 — shared base models, reference data, utils
    "apps.accounts",   # L2 — custom user, roles, permissions
    "apps.orders",     # L3 — customers, orders, stones
    "apps.identification",  # L3 — identification reports
    "apps.production",      # L3 — sonara, carving, lapidary
    "apps.billing",         # L3 — bills, payments, GePG
    "apps.certificates",    # L3 — certificates, verification
    "apps.dashboard",       # L4 — shell, nav, styleguide
    "apps.adminpanel",      # L4 — generic back-office at /manage/
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS


# ------------------------------------------------------------
# Middleware
# ------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.core.current_user.CurrentUserMiddleware",
    "auditlog.middleware.AuditlogMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# ------------------------------------------------------------
# Templates
# ------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.site",
                "apps.core.context_processors.breadcrumbs",
            ],
        },
    },
]


# ------------------------------------------------------------
# Database
# ------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": config("DB_ENGINE", default="django.db.backends.postgresql"),
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER", default=""),
        "PASSWORD": config("DB_PASSWORD", default=""),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
    }
}


# ------------------------------------------------------------
# Authentication
# ------------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"  # custom user model, set on day one

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard:home"
LOGOUT_REDIRECT_URL = "login"


# ------------------------------------------------------------
# Internationalization
# ------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = config("TIME_ZONE", default="Africa/Dar_es_Salaam")
USE_I18N = True
USE_TZ = True  # store timezone-aware datetimes


# ------------------------------------------------------------
# Static & media
# ------------------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# ------------------------------------------------------------
# Defaults
# ------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ------------------------------------------------------------
# Icons (django-iconify — self-hosted Iconify API for the web component)
# ------------------------------------------------------------
ICONIFY_JSON_ROOT = str(BASE_DIR / "node_modules" / "@iconify" / "json")


# ------------------------------------------------------------
# GePG (Government Electronic Payment Gateway)
# Secrets come from the environment; never commit real values.
# ------------------------------------------------------------
GEPG_BILL_CREATE_URL = config("GEPG_BILL_CREATE_URL", default="")
GEPG_BILL_CANCEL_URL = config("GEPG_BILL_CANCEL_URL", default="")
GEPG_RECONCILIATION_URL = config("GEPG_RECONCILIATION_URL", default="")

GEPG_SP_GRP_CODE = config("GEPG_SP_GRP_CODE", default="")
GEPG_SYS_CODE = config("GEPG_SYS_CODE", default="")
GEPG_SP_CODE = config("GEPG_SP_CODE", default="")
GEPG_SUB_SP_CODE = config("GEPG_SUB_SP_CODE", default="")
GEPG_COLL_CENT_CODE = config("GEPG_COLL_CENT_CODE", default="")
GEPG_GFS_CODE = config("GEPG_GFS_CODE", default="")

# Digital signature (PKCS#12 SHA256withRSA)
GEPG_USE_DIGITAL_SIGNATURE = config(
    "GEPG_USE_DIGITAL_SIGNATURE", default=False, cast=bool
)
GEPG_CERTIFICATE_PASSWORD = config("GEPG_CERTIFICATE_PASSWORD", default="")
GEPG_PRIVATE_KEY_PATH = config(
    "GEPG_PRIVATE_KEY_PATH", default=str(BASE_DIR / "certificates" / "private.pfx")
)
GEPG_PUBLIC_CERT_PATH = config(
    "GEPG_PUBLIC_CERT_PATH", default=str(BASE_DIR / "certificates" / "public.pfx")
)

# Bill defaults
GEPG_BILL_EXPIRY_DAYS = config("GEPG_BILL_EXPIRY_DAYS", default=365, cast=int)
