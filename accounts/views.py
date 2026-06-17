from django.conf import settings
from django.utils.decorators import method_decorator
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
        email_address = _get_or_create_email_address(user, verified=False)
        email_address.send_confirmation(request)
        return _jwt_response(user, http_status=status.HTTP_201_CREATED)


@method_decorator(ratelimit(key="ip", rate="10/m", method="POST", block=True), name="post")
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        # Backfill: old users have no EmailAddress record; create one and send the
        # first-ever verification email automatically on their next login.
        email_address = _get_or_create_email_address(user, verified=False)
        if not email_address.verified and email_address.emailconfirmation_set.count() == 0:
            email_address.send_confirmation(request)
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

        email_address.send_confirmation(request)
        return Response({"detail": "Verification email sent."})
