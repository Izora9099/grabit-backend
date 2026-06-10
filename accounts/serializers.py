from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from core.images import process_image_upload
from .models import User, Address, AgentKYCDocument


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ["email", "password", "first_name", "last_name", "role", "phone", "city"]

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value.lower()

    def create(self, validated_data):
        # Use email as username so Django's auth backend can authenticate by email
        validated_data["username"] = validated_data["email"]
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField(required=False)
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        identifier = data.get("identifier") or self.initial_data.get("email") or self.initial_data.get("username")
        password = data.get("password")

        if not identifier or not password:
            raise serializers.ValidationError("Must include 'email' or 'username' and 'password'.")

        request = self.context.get("request")
        user = authenticate(request=request, username=identifier.lower(), password=password)
        if not user:
            user = authenticate(request=request, username=identifier, password=password)
        if not user:
            try:
                u = User.objects.get(email__iexact=identifier)
                user = authenticate(request=request, username=u.username, password=password)
            except User.DoesNotExist:
                user = None

        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("This account has been deactivated.")
        return {"user": user}


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name",
            "role", "phone", "city", "avatar", "is_kyc_verified",
        ]
        read_only_fields = ["id", "role", "is_kyc_verified"]

    def validate_avatar(self, file):
        if file is None:
            return file
        try:
            return process_image_upload(file)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message)


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=6)

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def save(self):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ["id", "label", "line", "city", "is_primary"]


class AgentKYCDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentKYCDocument
        fields = ["id", "doc_type", "label", "file", "status", "reviewed_at", "created_at"]
        read_only_fields = ["id", "status", "reviewed_at", "created_at"]

    def validate_file(self, file):
        if file is None:
            return file
        # Only convert image files (identity / driving_license documents with photo IDs)
        # Skip PDFs — check magic bytes: PDF starts with %PDF (0x25 0x50 0x44 0x46)
        header = file.read(4)
        file.seek(0)
        if header == b"%PDF":
            return file  # PDFs pass through unchanged
        try:
            return process_image_upload(file)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message)


# ── Google OAuth ──────────────────────────────────────────────────────────────

class GoogleLoginSerializer(serializers.Serializer):
    """
    Accepts a Google ID token, verifies it via allauth's SocialApp mechanism,
    and returns (user, is_new).  Uses google-auth for token verification which
    is part of Google's official Python SDK — not raw OAuth implementation.
    """
    id_token = serializers.CharField()

    def validate(self, data):
        from allauth.socialaccount.models import SocialAccount, SocialApp
        from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter

        try:
            from google.oauth2 import id_token as google_id_token
            from google.auth.transport import requests as google_requests
        except ImportError:
            # google-auth not installed; fall back to allauth's token info endpoint
            return self._verify_via_tokeninfo(data)

        request = self.context["request"]

        # Resolve client_id from the configured SocialApp (stored via allauth admin or settings)
        try:
            adapter = GoogleOAuth2Adapter(request)
            app = adapter.get_provider().get_app(request)
            client_id = app.client_id
        except Exception:
            from django.conf import settings
            client_id = settings.SOCIALACCOUNT_PROVIDERS.get("google", {}).get(
                "APP", {}
            ).get("client_id", "")

        try:
            idinfo = google_id_token.verify_oauth2_token(
                data["id_token"],
                google_requests.Request(),
                client_id,
            )
        except ValueError as exc:
            raise serializers.ValidationError({"id_token": f"Invalid Google token: {exc}"})

        email = idinfo.get("email", "").lower()
        if not email:
            raise serializers.ValidationError({"id_token": "Token does not contain an email address."})
        if not idinfo.get("email_verified"):
            raise serializers.ValidationError({"id_token": "Google email address is not verified."})

        google_uid = idinfo["sub"]

        # Find existing social account or create user
        try:
            social = SocialAccount.objects.get(provider="google", uid=google_uid)
            user = social.user
            is_new = False
        except SocialAccount.DoesNotExist:
            # Get or create the Django user by email
            user, is_new = User.objects.get_or_create(
                email=email,
                defaults={
                    "username": email,
                    "first_name": idinfo.get("given_name", ""),
                    "last_name": idinfo.get("family_name", ""),
                    "is_active": True,
                },
            )
            SocialAccount.objects.create(
                user=user,
                provider="google",
                uid=google_uid,
                extra_data=idinfo,
            )

        if not user.is_active:
            raise serializers.ValidationError("This account has been deactivated.")

        return {"user": user, "is_new": is_new}

    def _verify_via_tokeninfo(self, data):
        """Fallback: verify the ID token using Google's tokeninfo endpoint."""
        import urllib.request, json
        from django.conf import settings

        token = data["id_token"]
        url = f"https://oauth2.googleapis.com/tokeninfo?id_token={token}"
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                idinfo = json.loads(resp.read())
        except Exception:
            raise serializers.ValidationError({"id_token": "Could not verify Google token."})

        if "error" in idinfo:
            raise serializers.ValidationError({"id_token": idinfo["error"]})

        if idinfo.get("email_verified") not in (True, "true"):
            raise serializers.ValidationError({"id_token": "Google email address is not verified."})

        expected_client_id = settings.SOCIALACCOUNT_PROVIDERS.get("google", {}).get("APP", {}).get("client_id", "")
        if expected_client_id and idinfo.get("aud") != expected_client_id:
            raise serializers.ValidationError({"id_token": "Token was not issued for this application."})

        from allauth.socialaccount.models import SocialAccount
        email = idinfo.get("email", "").lower()
        google_uid = idinfo["sub"]

        try:
            social = SocialAccount.objects.get(provider="google", uid=google_uid)
            user = social.user
            is_new = False
        except SocialAccount.DoesNotExist:
            user, is_new = User.objects.get_or_create(
                email=email,
                defaults={
                    "username": email,
                    "first_name": idinfo.get("given_name", ""),
                    "last_name": idinfo.get("family_name", ""),
                },
            )
            SocialAccount.objects.create(user=user, provider="google", uid=google_uid, extra_data=idinfo)

        return {"user": user, "is_new": is_new}


class GoogleCompleteSerializer(serializers.ModelSerializer):
    """Collect role, city, and phone from first-time Google sign-in users."""
    class Meta:
        model = User
        fields = ["role", "city", "phone"]
