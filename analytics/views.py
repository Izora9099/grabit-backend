from datetime import timedelta

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AnalyticsEvent


class VendorAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            shop = request.user.shop
        except Exception:
            return Response({"detail": "no_shop"}, status=404)

        period = min(int(request.query_params.get("period", 30)), 365)
        since = timezone.now() - timedelta(days=period)
        qs = AnalyticsEvent.objects.filter(shop=shop, created_at__gte=since)

        def _by_day(event_type):
            return [
                {"date": str(r["date"]), "count": r["count"]}
                for r in (
                    qs.filter(event_type=event_type)
                    .annotate(date=TruncDate("created_at"))
                    .values("date")
                    .annotate(count=Count("id"))
                    .order_by("date")
                )
            ]

        funnel_stages = [
            ("shop_visited",    "Shop visits"),
            ("product_viewed",  "Product views"),
            ("wishlist_added",  "Wishlisted"),
            ("order_placed",    "Orders placed"),
            ("order_paid",      "Paid"),
            ("order_completed", "Completed"),
        ]
        funnel_counts = {
            key: qs.filter(event_type=key).count()
            for key, _ in funnel_stages
        }

        visits_total  = funnel_counts["shop_visited"]
        orders_placed = funnel_counts["order_placed"]
        cvr = round(orders_placed / visits_total * 100, 1) if visits_total > 0 else 0.0

        repeat_buyers = (
            AnalyticsEvent.objects
            .filter(shop=shop, event_type="order_completed", user__isnull=False)
            .values("user")
            .annotate(cnt=Count("id"))
            .filter(cnt__gte=2)
            .count()
        )

        top_products = [
            {"id": r["product__id"], "name": r["product__name"], "views": r["views"]}
            for r in (
                qs.filter(event_type="product_viewed", product__isnull=False)
                .values("product__id", "product__name")
                .annotate(views=Count("id"))
                .order_by("-views")[:5]
            )
        ]

        return Response({
            "period": period,
            "shop_visits": {
                "total": visits_total,
                "by_day": _by_day("shop_visited"),
            },
            "product_views": {
                "total": funnel_counts["product_viewed"],
                "by_day": _by_day("product_viewed"),
            },
            "funnel": [
                {"stage": label, "count": funnel_counts[key]}
                for key, label in funnel_stages
            ],
            "cvr": cvr,
            "repeat_buyers": repeat_buyers,
            "top_products": top_products,
        })
