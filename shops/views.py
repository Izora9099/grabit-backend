from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Shop, ShopFollow, KYCDocument
from .serializers import ShopSerializer, ShopCreateSerializer, KYCDocumentSerializer
from products.models import Product
from products.serializers import ProductListSerializer


class ShopListView(generics.ListAPIView):
    queryset = Shop.objects.filter(status="active")
    serializer_class = ShopSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        city = self.request.query_params.get("city")
        category = self.request.query_params.get("category")
        if city:
            qs = qs.filter(city__iexact=city)
        if category:
            qs = qs.filter(category__iexact=category)
        return qs


class ShopDetailView(generics.RetrieveAPIView):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    permission_classes = [AllowAny]
    lookup_field = "handle"


class ShopProductsView(generics.ListAPIView):
    serializer_class = ProductListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Product.objects.filter(shop__handle=self.kwargs["handle"], status="live")


class ShopFollowView(APIView):
    def post(self, request, handle):
        shop = Shop.objects.get(handle=handle)
        follow, created = ShopFollow.objects.get_or_create(user=request.user, shop=shop)
        if created:
            shop.followers_count += 1
            shop.save(update_fields=["followers_count"])
            return Response({"following": True}, status=status.HTTP_201_CREATED)
        follow.delete()
        shop.followers_count = max(0, shop.followers_count - 1)
        shop.save(update_fields=["followers_count"])
        return Response({"following": False})


class MyShopView(generics.RetrieveUpdateAPIView):
    serializer_class = ShopSerializer

    def get_object(self):
        return self.request.user.shop

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return ShopCreateSerializer
        return ShopSerializer


class MyShopCreateView(generics.CreateAPIView):
    serializer_class = ShopCreateSerializer


class KYCDocumentListCreateView(generics.ListCreateAPIView):
    serializer_class = KYCDocumentSerializer
    pagination_class = None

    def _get_shop(self):
        try:
            return self.request.user.shop
        except Exception:
            from rest_framework.exceptions import NotFound
            raise NotFound("You don't have a shop yet. Please create one first at /sell.")

    def get_queryset(self):
        return KYCDocument.objects.filter(shop=self._get_shop())

    def perform_create(self, serializer):
        serializer.save(shop=self._get_shop())


class FollowedShopsView(generics.ListAPIView):
    serializer_class = ShopSerializer

    def get_queryset(self):
        followed_ids = ShopFollow.objects.filter(user=self.request.user).values_list("shop_id", flat=True)
        return Shop.objects.filter(id__in=followed_ids)