from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission


class IsEmailVerified(BasePermission):
    """
    Blocks authenticated users whose email address has not been confirmed.
    Returns a 403 with code='email_not_verified' so the frontend can show
    the verification prompt rather than a generic error.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        from allauth.account.models import EmailAddress
        if EmailAddress.objects.filter(user=request.user, verified=True).exists():
            return True
        raise PermissionDenied(
            detail={"code": "email_not_verified", "detail": "Please verify your email address to continue."}
        )
