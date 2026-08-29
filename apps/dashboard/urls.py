"""Dashboard URLs."""

from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("styleguide/", views.StyleguideView.as_view(), name="styleguide"),
    path("styleguide/htmx-demo/", views.htmx_demo, name="htmx_demo"),
]
