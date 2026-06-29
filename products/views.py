from rest_framework import generics, filters, status
from rest_framework.exceptions import NotFound
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Category, Product, ProductImage, Review, WishlistItem
from .serializers import (
    CategorySerializer, ProductDetailSerializer, ProductImageSerializer,
    ProductListSerializer, ProductWriteSerializer, ReviewSerializer, WishlistSerializer,
)


class CategoryListView(generics.ListAPIView):
    """Public: list active categories for use in product forms/filters."""
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    queryset = Category.objects.filter(is_active=True)


class ProductListView(generics.ListAPIView):
    serializer_class = ProductListSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description", "category__name"]
    ordering_fields = ["price", "rating", "created_at"]

    def get_queryset(self):
        qs = Product.objects.filter(status="live").select_related("shop", "category")
        category = self.request.query_params.get("category")
        city = self.request.query_params.get("city")
        condition = self.request.query_params.get("condition")
        min_price = self.request.query_params.get("min_price")
        max_price = self.request.query_params.get("max_price")
        if category:
            qs = qs.filter(category__slug__iexact=category)
        if city:
            qs = qs.filter(shop__city__iexact=city)
        if condition:
            qs = qs.filter(condition=condition)
        if min_price:
            qs = qs.filter(price__gte=min_price)
        if max_price:
            qs = qs.filter(price__lte=max_price)
        return qs


class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.filter(status="live").select_related("shop", "category")
    serializer_class = ProductDetailSerializer
    permission_classes = [AllowAny]

    def retrieve(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.views += 1
        obj.save(update_fields=["views"])
        try:
            from analytics.tasks import record_event
            record_event.delay(
                "product_viewed",
                obj.shop_id,
                obj.id,
                request.user.id if request.user.is_authenticated else None,
                request.session.session_key or "",
            )
        except Exception:
            pass
        return super().retrieve(request, *args, **kwargs)


_NO_SHOP = {"detail": "no_shop", "message": "You don't have a shop yet."}


class VendorProductListCreateView(generics.ListCreateAPIView):
    """Vendor-only: list & create their own products."""
    def get_serializer_class(self):
        if self.request.method == "POST":
            return ProductWriteSerializer
        return ProductListSerializer

    def get_queryset(self):
        try:
            return Product.objects.filter(shop=self.request.user.shop)
        except AttributeError:
            raise NotFound(_NO_SHOP)


class VendorProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductWriteSerializer

    def get_queryset(self):
        try:
            return Product.objects.filter(shop=self.request.user.shop)
        except AttributeError:
            raise NotFound(_NO_SHOP)


class ProductReviewListCreateView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer

    def get_permissions(self):
        return [AllowAny()] if self.request.method == "GET" else [IsAuthenticated()]

    def get_queryset(self):
        return Review.objects.filter(product_id=self.kwargs["pk"])

    def perform_create(self, serializer):
        serializer.save(buyer=self.request.user, product_id=self.kwargs["pk"])


class WishlistView(generics.ListCreateAPIView):
    serializer_class = WishlistSerializer

    def get_queryset(self):
        return WishlistItem.objects.filter(user=self.request.user).select_related("product")

    def perform_create(self, serializer):
        item = serializer.save(user=self.request.user)
        try:
            from analytics.tasks import record_event
            record_event.delay(
                "wishlist_added",
                item.product.shop_id,
                item.product_id,
                self.request.user.id,
                self.request.session.session_key or "",
            )
        except Exception:
            pass


class WishlistItemView(generics.DestroyAPIView):
    serializer_class = WishlistSerializer

    def get_queryset(self):
        return WishlistItem.objects.filter(user=self.request.user)


class ProductImageListCreateView(generics.ListCreateAPIView):
    """Vendor-only: list and upload images for one of their products."""
    serializer_class = ProductImageSerializer
    parser_classes = [MultiPartParser, FormParser]

    def _get_product(self):
        try:
            shop = self.request.user.shop
        except AttributeError:
            raise NotFound(_NO_SHOP)
        return get_object_or_404(Product, pk=self.kwargs["pk"], shop=shop)

    def get_queryset(self):
        return self._get_product().images.all()

    def perform_create(self, serializer):
        product = self._get_product()
        is_primary = not product.images.exists()
        serializer.save(product=product, is_primary=is_primary)


class ProductImageDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vendor-only: set-primary or delete a product image."""
    serializer_class = ProductImageSerializer
    lookup_url_kwarg = "img_pk"

    def get_queryset(self):
        try:
            shop = self.request.user.shop
        except AttributeError:
            raise NotFound(_NO_SHOP)
        return ProductImage.objects.filter(
            product_id=self.kwargs["pk"],
            product__shop=shop,
        )
