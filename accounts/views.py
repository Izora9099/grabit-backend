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
        return _jwt_response(user, http_status=status.HTTP_201_CREATED)


@method_decorator(ratelimit(key="ip", rate="10/m", method="POST", block=True), name="post")
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return _jwt_response(serializer.validated_data["user"])


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
