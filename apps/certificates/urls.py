"""Certificate URLs — staff management + a public verification page."""

from django.urls import path

from . import views

app_name = "certificates"

urlpatterns = [
    path("", views.CertificateListView.as_view(), name="index"),
    path("worklist/", views.CertificationWorklistView.as_view(), name="worklist"),
    path("stones/<int:stone_pk>/issue/", views.certificate_issue, name="issue"),
    path("verify/<str:token>/", views.certificate_verify, name="verify"),
    path("<int:pk>/", views.certificate_detail, name="detail"),
    path("<int:pk>/print/", views.certificate_print, name="print"),
    path("<int:pk>/revoke/", views.certificate_revoke, name="revoke"),
]
