"""Billing URLs — GePG inbound webhooks."""

from django.urls import path

from . import views

app_name = "billing"

urlpatterns = [
    path("api/payments/notification/", views.payment_notification, name="payment_notification"),
    path("api/bill/response/", views.bill_response, name="bill_response"),
]
