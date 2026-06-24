import re

from rest_framework import serializers
from .models import Payment, Payout, PlatformConfig


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["payment_id", "order", "method", "amount", "phone_number", "status", "external_ref", "created_at"]
        read_only_fields = ["payment_id", "amount", "status", "external_ref", "created_at"]


class InitiatePaymentSerializer(serializers.Serializer):
    order_id = serializers.CharField()
    method = serializers.ChoiceField(choices=["mtn_momo", "orange_money"])
    phone_number = serializers.CharField()

    def validate_phone_number(self, value):
        digits = re.sub(r"\D", "", value)
        if len(digits) == 12 and digits.startswith("237"):  # tolerate +237 prefix
            digits = digits[3:]
        if not re.fullmatch(r"6\d{8}", digits):
            raise serializers.ValidationError(
                "Enter a valid 9-digit Cameroonian mobile number (e.g. 6XXXXXXXX)."
            )
        return digits


class PayoutSerializer(serializers.ModelSerializer):
    recipient_name = serializers.CharField(source="recipient.get_full_name", read_only=True)

    class Meta:
        model = Payout
        fields = ["payout_id", "recipient_name", "method", "phone_number", "amount", "status", "payout_date", "created_at"]


class PlatformConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlatformConfig
        fields = [
            "starter_commission", "growth_commission", "premium_commission",
            "escrow_release_hours", "dispute_window_hours",
            "free_shop_max_products", "premium_shop_max_products",
            "max_images_per_listing", "updated_at",
        ]
        read_only_fields = ["updated_at"]


class PayoutRequestSerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=100)
    method = serializers.ChoiceField(choices=["mtn_momo", "orange_money"])
    phone = serializers.CharField()

    def validate_phone(self, value):
        digits = re.sub(r"\D", "", value)
        if len(digits) == 12 and digits.startswith("237"):
            digits = digits[3:]
        if not re.fullmatch(r"6\d{8}", digits):
            raise serializers.ValidationError(
                "Enter a valid 9-digit Cameroonian mobile number (e.g. 6XXXXXXXX)."
            )
        return digits
