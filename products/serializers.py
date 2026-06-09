from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.files.storage import default_storage
from rest_framework import serializers

from core.images import process_image_upload
from .models import Product, ProductImage, Review, WishlistItem
from shops.models import Shop


class ProductImageSerializer(serializers.ModelSerializer):
    # Write-only: accept the raw file; we convert it and store the URL ourselves.
    image_file = serializers.ImageField(write_only=True, required=False)

    class Meta:
        model = ProductImage
        fields = ["id", "image", "image_file", "is_primary", "order"]
        read_only_fields = ["id", "image"]

    def validate_image_file(self, file):
        if file is None:
            return file
        try:
            return process_image_upload(file)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message)

    def create(self, validated_data):
        image_file = validated_data.pop("image_file", None)
        if image_file:
            path = default_storage.save(f"products/{image_file.name}", image_file)
            validated_data["image"] = default_storage.url(path)
        elif not validated_data.get("image"):
            raise serializers.ValidationError({"image_file": "An image file is required."})
        return super().create(validated_data)

    def update(self, instance, validated_data):
        image_file = validated_data.pop("image_file", None)
        if image_file:
            path = default_storage.save(f"products/{image_file.name}", image_file)
            validated_data["image"] = default_storage.url(path)
        return super().update(instance, validated_data)


class ProductListSerializer(serializers.ModelSerializer):
    primary_image = serializers.SerializerMethodField()
    vendor = serializers.CharField(source="shop.name", read_only=True)
    vendor_id = serializers.CharField(source="shop.handle", read_only=True)
    city = serializers.CharField(source="shop.city", read_only=True)

    class Meta:
        model = Product
        fields = ["id", "name", "price", "category", "condition", "rating",
                  "reviews_count", "stock", "vendor", "vendor_id", "city",
                  "is_premium", "primary_image", "status"]

    def get_primary_image(self, obj):
        primary = obj.images.filter(is_primary=True).first()
        if primary:
            return primary.image
        first = obj.images.first()
        return first.image if first else None


class ProductDetailSerializer(ProductListSerializer):
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + ["description", "images", "views", "sales", "created_at"]


class ProductWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["name", "description", "price", "category", "condition", "stock", "status", "is_premium"]

    def create(self, validated_data):
        try:
            shop = self.context["request"].user.shop
        except AttributeError:
            from rest_framework.exceptions import NotFound
            raise NotFound({"detail": "no_shop", "message": "You don't have a shop yet."})
        return Product.objects.create(shop=shop, **validated_data)


class ReviewSerializer(serializers.ModelSerializer):
    buyer_name = serializers.CharField(source="buyer.get_full_name", read_only=True)

    class Meta:
        model = Review
        fields = ["id", "buyer_name", "rating", "text", "is_verified_purchase", "created_at"]
        read_only_fields = ["id", "buyer_name", "is_verified_purchase", "created_at"]


class WishlistSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), write_only=True, source="product")

    class Meta:
        model = WishlistItem
        fields = ["id", "product", "product_id", "created_at"]
        read_only_fields = ["id", "created_at"]
