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
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        # username field on our User model is stored as email
        user = authenticate(username=data["email"].lower(), password=data["password"])
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


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ["id", "label", "line", "city", "is_primary"]
