from rest_framework import serializers
from .models import Shop, ShopFollow, KYCDocument


class ShopSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source="owner.get_full_name", read_only=True)
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = Shop
        fields = [
            "id", "handle", "name", "tagline", "description", "category",
            "city", "neighbourhood", "logo", "banner", "accent_color",
            "whatsapp", "email", "delivery_fee", "free_shipping_threshold",
            "return_policy", "processing_time", "plan", "status",
            "is_verified", "followers_count", "rating", "reviews_count",
            "response_time", "joined", "owner_name", "is_following",
        ]
        read_only_fields = ["id", "handle", "status", "is_verified", "followers_count",
                            "rating", "reviews_count", "joined", "owner_name", "is_following"]

    def get_is_following(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return ShopFollow.objects.filter(user=request.user, shop=obj).exists()
        return False


class ShopCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ["name", "handle", "tagline", "description", "category", "city",
                  "neighbourhood", "whatsapp", "email", "delivery_fee",
                  "free_shipping_threshold", "return_policy", "processing_time"]

    def create(self, validated_data):
        return Shop.objects.create(owner=self.context["request"].user, **validated_data)


class KYCDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = KYCDocument
        fields = ["id", "doc_type", "label", "file", "status", "reviewed_at", "created_at"]
        read_only_fields = ["id", "status", "reviewed_at", "created_at"]
