from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from core.images import process_image_upload
from .models import Shop, ShopFollow, ShopReview, KYCDocument


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
                  "neighbourhood", "logo", "banner", "accent_color", "whatsapp",
                  "email", "delivery_fee", "free_shipping_threshold",
                  "return_policy", "processing_time"]

    def _convert_image(self, file):
        if file is None:
            return file
        try:
            return process_image_upload(file)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message)

    def validate_logo(self, file):
        return self._convert_image(file)

    def validate_banner(self, file):
        return self._convert_image(file)

    def create(self, validated_data):
        return Shop.objects.create(owner=self.context["request"].user, **validated_data)


class ShopReviewSerializer(serializers.ModelSerializer):
    buyer_name = serializers.CharField(source="buyer.get_full_name", read_only=True)

    class Meta:
        model = ShopReview
        fields = ["id", "buyer_name", "rating", "body", "created_at"]
        read_only_fields = ["id", "buyer_name", "created_at"]


class KYCDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = KYCDocument
        fields = ["id", "doc_type", "label", "file", "status", "reviewed_at", "created_at"]
        read_only_fields = ["id", "status", "reviewed_at", "created_at"]

    def validate_file(self, file):
        if file is None:
            return file
        # Let PDFs through unchanged; convert images to WebP
        header = file.read(4)
        file.seek(0)
        if header == b"%PDF":
            return file
        try:
            return process_image_upload(file)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message)
