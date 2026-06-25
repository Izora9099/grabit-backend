import logging

from django.conf import settings
from django.utils.decorators import method_decorator

logger = logging.getLogger(__name__)
from django_ratelimit.decorators import ratelimit
from rest_framework import generics, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from .models import Address, AgentKYCDocument

_ACTIVE_ORDER_STATUSES = {
    "awaiting_payment", "paid_escrow", "preparing", "agent_assigned",
    "picked_up", "in_transit", "delivered_confirm", "disputed",
}
from .serializers import (
    AddressSerializer, AgentKYCDocumentSerializer, ChangePasswordSerializer,
    GoogleCompleteSerializer, GoogleLoginSerializer, LoginSerializer,
    RegisterSerializer, UserSerializer,
)


def _get_or_create_email_address(user, verified=False):
    """Return the allauth EmailAddress for the user, creating it if missing."""
    from allauth.account.models import EmailAddress
    obj, _ = EmailAddress.objects.get_or_create(
        user=user,
        email=user.email,
        defaults={"primary": True, "verified": verified},
    )
    return obj


def _ensure_email_verified_for_google(user):
    """Mark a Google-auth user's email as verified (Google already confirmed it)."""
    from allauth.account.models import EmailAddress
    obj = _get_or_create_email_address(user, verified=True)
    if not obj.verified:
        obj.verified = True
        obj.save(update_fields=["verified"])

_COOKIE = settings.JWT_REFRESH_COOKIE_NAME
_MAX_AGE = settings.JWT_REFRESH_COOKIE_MAX_AGE


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """Attach the refresh token as an HttpOnly, SameSite=Strict cookie."""
    secure = getattr(settings, "JWT_REFRESH_COOKIE_SECURE", False)
    samesite = getattr(settings, "JWT_REFRESH_COOKIE_SAMESITE", "Strict")
    response.set_cookie(
        key=_COOKIE,
        value=refresh_token,
        max_age=_MAX_AGE,
        httponly=True,
        secure=secure,
        samesite=samesite,
    )


def _jwt_response(user, http_status=status.HTTP_200_OK) -> Response:
    """Create a standard JWT response: access token in body, refresh in cookie."""
    refresh = RefreshToken.for_user(user)
    response = Response(
        {"access": str(refresh.access_token), "user": UserSerializer(user).data},
        status=http_status,
    )
    _set_refresh_cookie(response, str(refresh))
    return response


@method_decorator(ratelimit(key="ip", rate="5/m", method="POST", block=True), name="post")
class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        try:
            email_address = _get_or_create_email_address(user, verified=False)
            email_address.send_confirmation(request)
        except BaseException:
            pass  # email failure never blocks registration
        return _jwt_response(user, http_status=status.HTTP_201_CREATED)


@method_decorator(ratelimit(key="ip", rate="10/m", method="POST", block=True), name="post")
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        try:
            # Backfill: old users have no EmailAddress record; create one and send the
            # first-ever verification email automatically on their next login.
            email_address = _get_or_create_email_address(user, verified=False)
            if not email_address.verified and email_address.emailconfirmation_set.count() == 0:
                email_address.send_confirmation(request)
        except BaseException:
            pass  # email failure never blocks login
        return _jwt_response(user)


class TokenRefreshView(APIView):
    """Read the refresh token from the HttpOnly cookie and issue a new access token."""
    permission_classes = [AllowAny]

    def post(self, request):
        raw = request.COOKIES.get(_COOKIE)
        if not raw:
            return Response({"detail": "No refresh token cookie."}, status=status.HTTP_401_UNAUTHORIZED)
        serializer = TokenRefreshSerializer(data={"refresh": raw})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError:
            return Response({"detail": "Invalid or expired refresh token."}, status=status.HTTP_401_UNAUTHORIZED)

        data = serializer.validated_data
        response = Response({"access": data["access"]})
        # If rotation produced a new refresh token, update the cookie
        if "refresh" in data:
            _set_refresh_cookie(response, data["refresh"])
        return response


class LogoutView(APIView):
    def post(self, request):
        raw = request.COOKIES.get(_COOKIE)
        if raw:
            try:
                RefreshToken(raw).blacklist()
            except TokenError:
                pass  # already blacklisted or invalid — still clear the cookie
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie(_COOKIE)
        return response


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password updated successfully."})


class AddressListCreateView(generics.ListCreateAPIView):
    serializer_class = AddressSerializer

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AddressSerializer

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)


class AgentKYCListCreateView(generics.ListCreateAPIView):
    """Agent-only: list and upload their own KYC documents."""
    serializer_class = AgentKYCDocumentSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    pagination_class = None

    def get_queryset(self):
        return AgentKYCDocument.objects.filter(agent=self.request.user)

    def perform_create(self, serializer):
        serializer.save(agent=self.request.user)


class AgentKYCDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Agent-only: retrieve, update or delete one of their KYC documents."""
    serializer_class = AgentKYCDocumentSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        return AgentKYCDocument.objects.filter(agent=self.request.user)


class AgentKYCSubmitView(APIView):
    """Agent submits all uploaded KYC docs for review."""
    def post(self, request):
        from django.utils import timezone
        pending = AgentKYCDocument.objects.filter(agent=request.user, status="draft")
        count = pending.count()
        if count == 0:
            return Response(
                {"detail": "No draft documents to submit. Please upload your documents first."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        pending.update(status="pending")
        return Response({"detail": f"{count} document(s) submitted for review. Our team will respond within 1–2 business days."})


# ── Google OAuth ──────────────────────────────────────────────────────────────

@method_decorator(ratelimit(key="ip", rate="10/m", method="POST", block=True), name="post")
class GoogleLoginView(APIView):
    """
    Accepts a Google ID token from the frontend, verifies it via allauth's
    Google adapter, and returns JWT tokens.  Sets profile_complete=False for
    first-time sign-ins so the frontend knows to show the GoogleCompleteForm.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GoogleLoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        is_new = serializer.validated_data["is_new"]

        # Google already verified the email — mark it so in our records.
        _ensure_email_verified_for_google(user)

        refresh = RefreshToken.for_user(user)
        response = Response({
            "access": str(refresh.access_token),
            "user": UserSerializer(user).data,
            "profile_complete": not is_new,
        })
        _set_refresh_cookie(response, str(refresh))
        return response


class GoogleCompleteView(APIView):
    """
    First-time Google users send role, city, and phone to complete their profile.
    Endpoint is protected — the frontend must send the access token from GoogleLoginView.
    """
    def post(self, request):
        serializer = GoogleCompleteSerializer(
            instance=request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)


# ── Email verification ────────────────────────────────────────────────────────

@method_decorator(ratelimit(key="ip", rate="5/m", method="POST", block=True), name="post")
class EmailVerifyConfirmView(APIView):
    """
    Frontend POSTs the key from the verification link here.
    POST /api/accounts/email/verify/confirm/  { "key": "<key from email link>" }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        from allauth.account.models import EmailConfirmationHMAC, EmailConfirmation

        key = request.data.get("key", "").strip()
        if not key:
            return Response({"detail": "Verification key is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Try HMAC-based key first (no DB lookup needed)
        confirmation = EmailConfirmationHMAC.from_key(key)

        # Fall back to DB-stored key (older allauth flow)
        if confirmation is None:
            try:
                confirmation = EmailConfirmation.objects.get(key=key)
            except EmailConfirmation.DoesNotExist:
                confirmation = None

        if confirmation is None:
            return Response({"detail": "Invalid or expired verification link."}, status=status.HTTP_400_BAD_REQUEST)

        confirmation.confirm(request)
        return Response({"detail": "Email verified successfully."})


@method_decorator(ratelimit(key="user_or_ip", rate="3/m", method="POST", block=True), name="post")
class EmailVerifyResendView(APIView):
    """
    Authenticated users can request a fresh verification email.
    POST /api/accounts/email/verify/resend/
    """

    def post(self, request):
        from allauth.account.models import EmailAddress
        try:
            email_address = EmailAddress.objects.get(user=request.user, email=request.user.email)
        except EmailAddress.DoesNotExist:
            email_address = _get_or_create_email_address(request.user, verified=False)

        if email_address.verified:
            return Response({"detail": "Your email is already verified."})

        try:
            email_address.send_confirmation(request)
        except BaseException:
            pass  # email failure never blocks the response
        return Response({"detail": "Verification email sent."})


# ── Password reset ───────────────────────────────────────────────────────────

@method_decorator(ratelimit(key="ip", rate="5/m", method="POST", block=True), name="post")
class PasswordResetRequestView(APIView):
    """
    POST { "email": "..." }
    Always returns 200 to avoid leaking whether an email exists.
    Sends a password-reset link via Mailtrap if the address is registered.
    Link format: {FRONTEND_URL}/reset-password?uid=<uid_b64>&token=<token>
    """
    permission_classes = [AllowAny]

    def post(self, request):
        from django.contrib.auth import get_user_model
        from django.contrib.auth.tokens import default_token_generator
        from django.core.mail import EmailMultiAlternatives
        from django.template.loader import render_to_string
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        email = request.data.get("email", "").strip().lower()
        frontend_url = getattr(settings, "FRONTEND_URL", "https://grabit.sale")

        User = get_user_model()
        try:
            user = User.objects.get(email__iexact=email, is_active=True)
        except User.DoesNotExist:
            # Return success regardless to avoid email enumeration
            return Response({"detail": "If that address is registered you will receive a reset link shortly."})

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_url = f"{frontend_url}/reset-password?uid={uid}&token={token}"

        context = {
            "first_name": user.first_name,
            "reset_url": reset_url,
            "frontend_url": frontend_url,
        }
        html_body = render_to_string("account/email/password_reset_message.html", context)
        text_body = (
            f"Hi {user.first_name or 'there'},\n\n"
            f"Reset your GrabIT password by visiting this link:\n{reset_url}\n\n"
            "The link expires in 30 minutes.\n\n"
            "If you didn't request this, ignore this email."
        )

        msg = EmailMultiAlternatives(
            subject="Reset your GrabIT password",
            body=text_body,
            from_email="GrabIT <no-reply@grabit.sale>",
            to=[user.email],
        )
        msg.attach_alternative(html_body, "text/html")
        try:
            msg.send(fail_silently=False)
        except Exception as exc:
            logger.warning("Password reset email failed for user %s: %s", user.pk, exc)

        return Response({"detail": "If that address is registered you will receive a reset link shortly."})


@method_decorator(ratelimit(key="ip", rate="10/m", method="POST", block=True), name="post")
class PasswordResetConfirmView(APIView):
    """
    POST { "uid": "...", "token": "...", "new_password": "..." }
    Validates the Django-generated token, sets the new password, and
    blacklists any outstanding refresh tokens via simplejwt's blacklist.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        from django.contrib.auth import get_user_model
        from django.contrib.auth.tokens import default_token_generator
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError as DjangoValidationError
        from django.utils.encoding import force_str
        from django.utils.http import urlsafe_base64_decode

        uid = request.data.get("uid", "").strip()
        token = request.data.get("token", "").strip()
        new_password = request.data.get("new_password", "").strip()

        if not uid or not token or not new_password:
            return Response(
                {"detail": "uid, token, and new_password are all required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        User = get_user_model()
        try:
            pk = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=pk, is_active=True)
        except Exception:
            return Response(
                {"detail": "Invalid or expired reset link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {"detail": "Invalid or expired reset link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_password(new_password, user)
        except DjangoValidationError as exc:
            return Response(
                {"detail": " ".join(exc.messages)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save(update_fields=["password"])

        # Invalidate all outstanding refresh tokens for this user
        try:
            from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
            from rest_framework_simplejwt.tokens import RefreshToken as _RefreshToken
            for ot in OutstandingToken.objects.filter(user=user):
                try:
                    _RefreshToken(ot.token).blacklist()
                except Exception as exc:
                    logger.warning("Could not blacklist token %s for user %s: %s", ot.pk, user.pk, exc)
        except Exception as exc:
            logger.warning("Token blacklist unavailable after password reset for user %s: %s", user.pk, exc)

        return Response({"detail": "Password reset successfully. You can now sign in."})


# ── Account deletion ──────────────────────────────────────────────────────────

@method_decorator(ratelimit(key="user_or_ip", rate="5/h", method="DELETE", block=True), name="delete")
class DeleteAccountView(APIView):
    """
    Soft-deletes the account: anonymises PII, deactivates it, and blacklists
    the refresh token. The user row is kept for order record integrity.

    Blocked if there are any active/in-progress orders to prevent fraud
    (e.g. scamming then vanishing before resolution).
    """
    def delete(self, request):
        user = request.user
        password = request.data.get("password", "").strip()

        if user.has_usable_password():
            if not password:
                return Response(
                    {"detail": "Your password is required to delete your account."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not user.check_password(password):
                return Response(
                    {"detail": "Incorrect password."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        from orders.models import Order

        if Order.objects.filter(buyer=user, status__in=_ACTIVE_ORDER_STATUSES).exists():
            return Response(
                {"detail": "You have active orders. Wait for them to complete or be resolved before deleting your account."},
                status=status.HTTP_409_CONFLICT,
            )

        try:
            from shops.models import Shop
            vendor_shops = Shop.objects.filter(owner=user)
            if vendor_shops.exists() and Order.objects.filter(
                shop__in=vendor_shops, status__in=_ACTIVE_ORDER_STATUSES
            ).exists():
                return Response(
                    {"detail": "Your shop has active orders. Wait for them to complete or be resolved before deleting your account."},
                    status=status.HTTP_409_CONFLICT,
                )
        except Exception as exc:
            logger.warning("Could not check active vendor orders for user %s during account deletion: %s", user.pk, exc)

        # Anonymise PII — row stays for order integrity and fraud traceability
        user.email = f"deleted_{user.pk}@deleted.invalid"
        user.first_name = "Deleted"
        user.last_name = "User"
        user.phone = ""
        user.city = ""
        user.avatar = None
        user.is_active = False
        user.set_unusable_password()
        user.save(update_fields=[
            "email", "first_name", "last_name", "phone",
            "city", "avatar", "is_active", "password",
        ])

        try:
            from allauth.account.models import EmailAddress
            EmailAddress.objects.filter(user=user).delete()
        except Exception as exc:
            logger.error("Failed to delete EmailAddress records for user %s: %s", user.pk, exc)

        try:
            from shops.models import Shop
            Shop.objects.filter(owner=user).update(status="closed")
        except Exception as exc:
            logger.error("Failed to close shops for deleted user %s: %s", user.pk, exc)

        raw = request.COOKIES.get(_COOKIE)
        if raw:
            try:
                RefreshToken(raw).blacklist()
            except Exception as exc:
                logger.warning("Could not blacklist refresh token on account deletion for user %s: %s", user.pk, exc)

        response = Response({"detail": "Account deleted."}, status=status.HTTP_200_OK)
        response.delete_cookie(_COOKIE)
        return response
