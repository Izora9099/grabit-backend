from rest_framework import serializers
from .models import Dispute


class DisputeSerializer(serializers.ModelSerializer):
    order_id = serializers.CharField(source="order.order_id", read_only=True)
    opened_by_name = serializers.CharField(source="opened_by.get_full_name", read_only=True)

    class Meta:
        model = Dispute
        fields = [
            "dispute_id", "order", "order_id", "opened_by_name", "reason",
            "description", "evidence", "status", "resolution", "admin_note",
            "created_at", "resolved_at",
        ]
        read_only_fields = ["dispute_id", "status", "resolution", "admin_note", "resolved_at", "opened_by_name"]


class DisputeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dispute
        fields = ["order", "reason", "description", "evidence"]

    def create(self, validated_data):
        validated_data["order"].status = "disputed"
        validated_data["order"].save(update_fields=["status"])
        return Dispute.objects.create(opened_by=self.context["request"].user, **validated_data)
