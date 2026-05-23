from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from .models import User, Address


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
        user = User.objects.create_user(**validated_data)
        Token.objects.create(user=user)
        return user


class LoginSerializer(serializers.Serializer):
    # Accept a single identifier (email or username). We don't declare an EmailField
    # so clients sending a non-email username in the 'email' key won't fail validation.
    identifier = serializers.CharField(required=False)
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        # Prefer declared `identifier`, fall back to raw initial data keys for
        # backwards compatibility with clients sending `email` or `username`.
        identifier = data.get("identifier") or self.initial_data.get("email") or self.initial_data.get("username")
        password = data.get("password")

        if not identifier or not password:
            raise serializers.ValidationError("Must include 'email' or 'username' and 'password'.")

        # Try authenticating using several strategies:
        # 1. As lowercase (common when username is an email)
        # 2. As provided
        # 3. Lookup by email and authenticate using that user's username
        user = authenticate(username=identifier.lower(), password=password)
        if not user:
            user = authenticate(username=identifier, password=password)
        if not user:
            try:
                u = User.objects.get(email__iexact=identifier)
                user = authenticate(username=u.username, password=password)
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
