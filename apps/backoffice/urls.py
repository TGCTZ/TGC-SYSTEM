"""Admin-panel URLs.

Specific routes (dashboard, activity, roles) come before the generic
``<app_label>/<model_name>/`` model routes so they aren't shadowed.
"""

from django.urls import path

from . import roles, views

app_name = "backoffice"

urlpatterns = [
    path("", views.index, name="index"),
    path("activity/", views.activity, name="activity"),
    # Roles & permissions portal
    path("roles/", roles.role_list, name="role_list"),
    path("roles/new/", roles.role_create, name="role_create"),
    path("roles/<int:pk>/", roles.role_detail, name="role_detail"),
    path("roles/<int:pk>/edit/", roles.role_edit, name="role_edit"),
    path("roles/<int:pk>/delete/", roles.role_delete, name="role_delete"),
    # Generic model CRUD
    path("<str:app_label>/<str:model_name>/", views.object_list, name="list"),
    path("<str:app_label>/<str:model_name>/new/", views.object_create, name="create"),
    path(
        "<str:app_label>/<str:model_name>/<int:pk>/", views.object_detail, name="detail"
    ),
    path(
        "<str:app_label>/<str:model_name>/<int:pk>/edit/",
        views.object_edit,
        name="edit",
    ),
    path(
        "<str:app_label>/<str:model_name>/<int:pk>/delete/",
        views.object_delete,
        name="delete",
    ),
]
