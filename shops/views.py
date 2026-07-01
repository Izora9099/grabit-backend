from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Avg, Count
from .models import Shop, ShopFollow, ShopReview, KYCDocument
from .serializers import ShopSerializer, ShopCreateSerializer, ShopReviewSerializer, KYCDocumentSerializer
from products.models import Product
from products.serializers import ProductListSerializer
from accounts.permissions import IsEmailVerified


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

    def retrieve(self, request, *args, **kwargs):
        obj = self.get_object()
        try:
            from analytics.tasks import record_event
            record_event.delay(
                "shop_visited",
                obj.id,
                None,
                request.user.id if request.user.is_authenticated else None,
                request.session.session_key or "",
            )
        except Exception:
            pass
        serializer = self.get_serializer(obj)
        return Response(serializer.data)


class ShopProductsView(generics.ListAPIView):
    serializer_class = ProductListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Product.objects.filter(shop__handle=self.kwargs["handle"], status="live")


class ShopFollowView(APIView):
    def post(self, request, handle):
        shop = get_object_or_404(Shop, handle=handle)
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
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self):
        try:
            return self.request.user.shop
        except AttributeError:
            raise NotFound({"detail": "no_shop", "message": "You don't have a shop yet."})

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return ShopCreateSerializer
        return ShopSerializer


class MyShopCreateView(generics.CreateAPIView):
    serializer_class = ShopCreateSerializer
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def create(self, request, *args, **kwargs):
        if hasattr(request.user, "shop"):
            if request.user.role != "vendor":
                request.user.role = "vendor"
                request.user.save(update_fields=["role"])
            return Response(
                {"detail": "You already have a shop.", "code": "shop_exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save()
        user = self.request.user
        if user.role != "vendor":
            user.role = "vendor"
            user.save(update_fields=["role"])


class KYCDocumentListCreateView(generics.ListCreateAPIView):
    serializer_class = KYCDocumentSerializer
    pagination_class = None
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def _get_shop(self):
        try:
            return self.request.user.shop
        except Exception:
            from rest_framework.exceptions import NotFound
            raise NotFound("You don't have a shop yet. Please create one first at /sell.")

    def get_queryset(self):
        return KYCDocument.objects.filter(shop=self._get_shop())

    def perform_create(self, serializer):
        serializer.save(shop=self._get_shop(), status="pending")


class KYCDocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = KYCDocumentSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        try:
            return KYCDocument.objects.filter(shop=self.request.user.shop)
        except Exception:
            return KYCDocument.objects.none()


class KYCSubmitView(APIView):
    """Vendor submits uploaded KYC docs for review."""
    def post(self, request):
        try:
            shop = request.user.shop
        except Exception:
            return Response({"detail": "No shop found."}, status=status.HTTP_404_NOT_FOUND)
        if shop.is_verified:
            return Response({"detail": "Shop is already verified."}, status=status.HTTP_400_BAD_REQUEST)
        if shop.status == "under_review":
            return Response({"detail": "Application already under review."}, status=status.HTTP_400_BAD_REQUEST)
        # On resubmission after rejection, clear old rejected docs so the admin
        # queue only shows the fresh set of documents.
        if shop.status == "rejected":
            KYCDocument.objects.filter(shop=shop, status="rejected").delete()
        pending_count = KYCDocument.objects.filter(shop=shop, status="pending").count()
        if pending_count == 0:
            return Response({"detail": "No documents uploaded. Please upload at least one document first."}, status=status.HTTP_400_BAD_REQUEST)
        shop.status = "under_review"
        shop.save(update_fields=["status"])
        return Response({"detail": "Submitted for review. Our team will respond within 1–2 business days."})


class ProSellerApplyView(APIView):
    """Vendor applies for Pro Seller status (tier 2)."""
    def post(self, request):
        try:
            shop = request.user.shop
        except Exception:
            return Response({"detail": "No shop found."}, status=status.HTTP_404_NOT_FOUND)
        if shop.tier == "pro_seller":
            return Response({"detail": "Shop is already a Pro Seller."}, status=status.HTTP_400_BAD_REQUEST)
        if shop.tier != "verified":
            return Response({"detail": "You must be a Verified seller before applying."}, status=status.HTTP_400_BAD_REQUEST)
        if shop.tier2_application_status == "pending":
            return Response({"detail": "Application already under review."}, status=status.HTTP_400_BAD_REQUEST)
        shop.tier2_application_status = "pending"
        shop.save(update_fields=["tier2_application_status"])
        return Response({"detail": "Application submitted. Our team will review within 3–5 business days."})


class FollowedShopsView(generics.ListAPIView):
    serializer_class = ShopSerializer

    def get_queryset(self):
        followed_ids = ShopFollow.objects.filter(user=self.request.user).values_list("shop_id", flat=True)
        return Shop.objects.filter(id__in=followed_ids)


class ShopReviewListCreateView(generics.ListCreateAPIView):
    serializer_class = ShopReviewSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated(), IsEmailVerified()]

    def get_queryset(self):
        return ShopReview.objects.filter(shop__handle=self.kwargs["handle"])

    def perform_create(self, serializer):
        shop = Shop.objects.get(handle=self.kwargs["handle"])
        serializer.save(buyer=self.request.user, shop=shop)
        agg = ShopReview.objects.filter(shop=shop).aggregate(avg=Avg("rating"), count=Count("id"))
        shop.rating = round(agg["avg"] or 0, 2)
        shop.reviews_count = agg["count"]
        shop.save(update_fields=["rating", "reviews_count"])