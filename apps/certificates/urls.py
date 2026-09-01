"""Certificate URLs — staff management + a public verification page."""

from django.urls import path

from . import views

app_name = "certificates"

urlpatterns = [
    path("", views.CertificateListView.as_view(), name="index"),
    path("worklist/", views.CertifiableStonesView.as_view(), name="worklist"),
    path("stones/<int:stone_pk>/issue/", views.issue, name="issue"),
    path("verify/<str:token>/", views.verify, name="verify"),
    path("<int:pk>/", views.detail, name="detail"),
    path("<int:pk>/print/", views.print_certificate, name="print"),
    path("<int:pk>/revoke/", views.revoke, name="revoke"),
]
