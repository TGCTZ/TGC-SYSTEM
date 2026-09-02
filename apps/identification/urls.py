"""Identification URLs."""

from django.urls import path

from . import views

app_name = "identification"

urlpatterns = [
    path("", views.IdentificationWorklistView.as_view(), name="index"),
    path("findings/", views.FindingsWorklistView.as_view(), name="findings"),
    path("findings/<int:pk>/", views.findings_edit, name="findings_edit"),
    path("report/<int:pk>/finalize/", views.report_finalize, name="finalize"),
    path("<int:order_pk>/", views.order_identify, name="order_identify"),
]
