"""Authentication views."""

from django.contrib.auth.views import LoginView


class AppLoginView(LoginView):
    """Sign-in page, rendered with the guest layout."""

    template_name = "pages/auth/login.html"
    redirect_authenticated_user = True
