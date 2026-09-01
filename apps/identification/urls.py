"""Identification URLs."""

from django.urls import path

from . import views

app_name = "identification"

urlpatterns = [
    path("", views.WorklistView.as_view(), name="index"),
    path("findings/", views.FindingsWorklistView.as_view(), name="findings"),
    path("findings/<int:pk>/", views.stone_findings, name="findings_stone"),
    path("report/<int:pk>/finalize/", views.finalize, name="finalize"),
    path("<int:order_pk>/", views.order_identify, name="order"),
]
