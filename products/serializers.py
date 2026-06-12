from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from core.images import process_image_upload
from .models import Category, Product, ProductImage, Review, WishlistItem
from shops.models import Shop


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "is_active"]
        read_only_fields = ["id"]

    def validate_name(self, value):
        from django.utils.text import slugify
        slug = slugify(value)
        qs = Category.objects.filter(slug=slug)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A category with this name already exists.")
        return value

    def create(self, validated_data):
        from django.utils.text import slugify
        validated_data.setdefault("slug", slugify(validated_data["name"]))
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "name" in validated_data and not validated_data.get("slug"):
            from django.utils.text import slugify
            validated_data["slug"] = slugify(validated_data["name"])
        return super().update(instance, validated_data)


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image", "is_primary", "order"]
        read_only_fields = ["id"]

    def validate_image(self, file):
        try:
            return process_image_upload(file)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message)


class ProductListSerializer(serializers.ModelSerializer):
    primary_image = serializers.SerializerMethodField()
    vendor = serializers.CharField(source="shop.name", read_only=True)
    vendor_id = serializers.CharField(source="shop.handle", read_only=True)
    city = serializers.CharField(source="shop.city", read_only=True)
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Product
        fields = ["id", "name", "price", "category", "condition", "rating",
                  "reviews_count", "stock", "vendor", "vendor_id", "city",
                  "is_premium", "primary_image", "status"]

    def get_primary_image(self, obj):
        primary = obj.images.filter(is_primary=True).first()
        if primary:
            return primary.image.url
        first = obj.images.first()
        return first.image.url if first else None


class ProductDetailSerializer(ProductListSerializer):
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + ["description", "images", "views", "sales", "created_at"]


class ProductWriteSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.filter(is_active=True))

    class Meta:
        model = Product
        fields = ["id", "name", "description", "price", "category", "condition", "stock", "status", "is_premium"]
        read_only_fields = ["id"]

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
