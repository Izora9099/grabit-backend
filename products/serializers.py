from rest_framework import serializers
from .models import Product, ProductImage, Review, WishlistItem
from shops.models import Shop


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image", "is_primary", "order"]


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
