"""Authentication URLs. Unnamespaced so `login`/`logout` resolve globally."""

from django.contrib.auth.views import LogoutView
from django.urls import path

from apps.accounts.views.auth import AppLoginView

urlpatterns = [
    path("login/", AppLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
