"""User-management URLs (namespaced ``users``).

Kept separate from ``urls.py`` (which owns the unnamespaced ``login``/``logout``)
so the CRUD module gets its own ``users:`` namespace.
"""

from django.urls import path

from . import users_views as views

app_name = "users"

urlpatterns = [
    path("", views.UserListView.as_view(), name="index"),
    path("new/", views.user_create, name="create"),
    path("<int:pk>/", views.UserDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.user_edit, name="edit"),
    path("<int:pk>/toggle/", views.user_toggle_active, name="toggle"),
    path("<int:pk>/delete/", views.user_delete, name="delete"),
]
