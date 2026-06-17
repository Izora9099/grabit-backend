from django.conf import settings
from allauth.account.adapter import DefaultAccountAdapter


class AccountAdapter(DefaultAccountAdapter):
    """
    Overrides the email-confirmation link so it points at the React frontend
    instead of Django's own confirmation view. The frontend reads the ?key=
    param and POSTs it to /api/accounts/email/verify/confirm/.
    """

    def get_email_confirmation_url(self, request, emailconfirmation):
        frontend_url = getattr(settings, "FRONTEND_URL", "https://grabit.sale")
        return f"{frontend_url}/verify-email/?key={emailconfirmation.key}"
