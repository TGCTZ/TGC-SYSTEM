"""Identification URLs."""

from django.urls import path

from . import views

app_name = "identification"

urlpatterns = [
    path("", views.WorklistView.as_view(), name="index"),
    path("<int:order_pk>/", views.order_identify, name="order"),
    path("stone/<int:pk>/edit/", views.stone_edit, name="edit"),
    path("report/<int:pk>/finalize/", views.finalize, name="finalize"),
]
