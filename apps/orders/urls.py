"""Reception (orders) URLs."""

from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("", views.OrderListView.as_view(), name="index"),
    path("new/", views.order_create, name="create"),
    path("<int:pk>/", views.OrderDetailView.as_view(), name="detail"),
]
