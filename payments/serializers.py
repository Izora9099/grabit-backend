from rest_framework import serializers
from .models import Payment, Payout


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["payment_id", "order", "method", "amount", "phone_number", "status", "external_ref", "created_at"]
        read_only_fields = ["payment_id", "amount", "status", "external_ref", "created_at"]


class InitiatePaymentSerializer(serializers.Serializer):
    order_id = serializers.CharField()
    method = serializers.ChoiceField(choices=["mtn_momo", "orange_money", "bank_transfer"])
    phone_number = serializers.CharField(required=False)


class PayoutSerializer(serializers.ModelSerializer):
    recipient_name = serializers.CharField(source="recipient.get_full_name", read_only=True)

    class Meta:
        model = Payout
        fields = ["payout_id", "recipient_name", "method", "amount", "status", "payout_date", "created_at"]
