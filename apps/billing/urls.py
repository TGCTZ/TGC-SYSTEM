"""Billing URLs — staff bill management + GePG inbound webhooks."""

from django.urls import path

from . import views

app_name = "billing"

urlpatterns = [
    # Staff-facing
    path("", views.BillListView.as_view(), name="index"),
    path("worklist/", views.BillableOrdersView.as_view(), name="worklist"),
    path("payments/", views.PaymentListView.as_view(), name="payments"),
    path("payments/<int:pk>/", views.payment_detail, name="payment_detail"),
    path("orders/<int:order_pk>/generate/", views.generate_bill, name="generate"),
    path("<int:pk>/", views.bill_detail, name="detail"),
    # GePG inbound webhooks
    path(
        "api/payments/notification/",
        views.payment_notification,
        name="payment_notification",
    ),
    path("api/bill/response/", views.bill_response, name="bill_response"),
]
