"""Root URL configuration. Includes app URLconfs; no view logic here."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("icons/", include("dj_iconify.urls")),
    path("billing/", include("apps.billing.urls")),
    path("", include("apps.dashboard.urls")),
]

# Serve media from the dev server only. Static files are handled by the
# staticfiles app in development and a real web server in production.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
