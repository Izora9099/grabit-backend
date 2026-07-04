from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    """
    Gates marketplace admin endpoints on `request.user.role == "admin"`.
    Distinct from DRF's `IsAdminUser`, which checks `is_staff` — a separate,
    Django-admin-site concept that isn't tied to the marketplace role field.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "admin")


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
