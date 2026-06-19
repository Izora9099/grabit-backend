"""
Admin-only API views. All views check request.user.role == 'admin'.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Q
from django.utils import timezone
import datetime

from .models import User
from .serializers import UserSerializer


def admin_required(view_func):
    """Simple inline decorator — returns 403 if not admin."""
    from functools import wraps
    @wraps(view_func)
    def wrapper(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != "admin":
            return Response({"detail": "Admin only."}, status=403)
        return view_func(self, request, *args, **kwargs)
    return wrapper


class AdminStatsView(APIView):
    """Overall platform KPIs."""
    @admin_required
    def get(self, request):
        from orders.models import Order
        from shops.models import Shop
        from payments.models import Payment

        today = timezone.now().date()
        month_start = today.replace(day=1)

        gmv_month = Payment.objects.filter(
            status="paid", created_at__date__gte=month_start
        ).aggregate(total=Sum("amount"))["total"] or 0

        gmv_total = Payment.objects.filter(status="paid").aggregate(
            total=Sum("amount")
        )["total"] or 0

        return Response({
            "total_users": User.objects.count(),
            "total_vendors": User.objects.filter(role="vendor").count(),
            "total_buyers": User.objects.filter(role="buyer").count(),
            "total_agents": User.objects.filter(role="agent").count(),
            "active_shops": Shop.objects.filter(status="active").count(),
            "pending_kyc": Shop.objects.filter(status="under_review").count(),
            "orders_today": Order.objects.filter(placed_at__date=today).count(),
            "gmv_month": gmv_month,
            "gmv_total": gmv_total,
            "open_disputes": __import__("disputes").models.Dispute.objects.filter(
                status="open"
            ).count(),
        })


class AdminUserListView(generics.ListAPIView):
    serializer_class = UserSerializer

    @admin_required
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        qs = User.objects.all().order_by("-date_joined")
        role = self.request.query_params.get("role")
        q = self.request.query_params.get("q")
        if role:
            qs = qs.filter(role=role)
        if q:
            qs = qs.filter(Q(username__icontains=q) | Q(email__icontains=q))
        return qs


class AdminUserDetailView(APIView):
    @admin_required
    def get(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)
        data = UserSerializer(user).data
        data["is_active"] = user.is_active
        data["date_joined"] = user.date_joined
        return Response(data)

    @admin_required
    def patch(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)
        for field in ("is_active", "role", "is_kyc_verified"):
            if field in request.data:
                setattr(user, field, request.data[field])
        user.save()
        data = UserSerializer(user).data
        data["is_active"] = user.is_active
        data["date_joined"] = user.date_joined
        return Response(data)


class AdminGMVView(APIView):
    @admin_required
    def get(self, request):
        from payments.models import Payment
        from django.db.models.functions import TruncDate
        import datetime

        # Last 30 days daily GMV
        cutoff = timezone.now() - datetime.timedelta(days=30)
        daily = (
            Payment.objects.filter(status="paid", created_at__gte=cutoff)
            .annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(gmv=Sum("amount"), orders=Count("id"))
            .order_by("date")
        )

        # Top vendors by revenue
        from orders.models import Order
        from shops.models import Shop
        top_vendors = (
            Order.objects.filter(status="completed")
            .values("shop__name", "shop__handle")
            .annotate(revenue=Sum("total"), order_count=Count("id"))
            .order_by("-revenue")[:10]
        )

        return Response({
            "daily": list(daily),
            "top_vendors": list(top_vendors),
        })


class AdminOrderListView(APIView):
    @admin_required
    def get(self, request):
        from orders.models import Order

        qs = Order.objects.select_related(
            "buyer", "shop", "agent"
        ).order_by("-placed_at")

        status_filter = request.query_params.get("status")
        q = request.query_params.get("q")

        if status_filter:
            qs = qs.filter(status=status_filter)
        if q:
            qs = qs.filter(
                Q(order_id__icontains=q) |
                Q(buyer__username__icontains=q) |
                Q(buyer__email__icontains=q)
            )

        data = [
            {
                "order_id": o.order_id,
                "status": o.status,
                "city": o.city,
                "total": o.total,
                "placed_at": o.placed_at,
                "updated_at": o.updated_at,
                "escrow_released": o.escrow_released,
                "buyer_name": o.buyer.get_full_name() if o.buyer_id else "",
                "buyer_email": o.buyer.email if o.buyer_id else "",
                "shop_name": o.shop.name if o.shop_id else "",
                "agent_name": o.agent.get_full_name() if o.agent_id else None,
            }
            for o in qs
        ]

        return Response(data)


class AdminShopListView(APIView):
    @admin_required
    def get(self, request):
        from shops.models import Shop
        from shops.serializers import ShopSerializer
        q = request.query_params.get("q", "")
        qs = Shop.objects.all().order_by("-id")
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(handle__icontains=q))
        return Response(ShopSerializer(qs, many=True).data)


class AdminVerificationQueueView(APIView):
    @admin_required
    def get(self, request):
        from shops.models import KYCDocument, Shop
        from shops.serializers import KYCDocumentSerializer
        pending_shops = Shop.objects.filter(
            status="under_review"
        ).select_related("owner").prefetch_related("kyc_documents")
        result = []
        for shop in pending_shops:
            docs = KYCDocument.objects.filter(shop=shop, status="pending").order_by("created_at")
            # Use when the first pending doc was uploaded as the submission timestamp.
            first_doc = docs.first()
            submitted_at = first_doc.created_at.isoformat() if first_doc else shop.created_at.isoformat()
            result.append({
                "shop_id": shop.id,
                "shop_name": shop.name,
                "shop_handle": shop.handle,
                "owner": shop.owner.get_full_name() or shop.owner.username,
                "owner_email": shop.owner.email,
                "submitted_at": submitted_at,
                "documents": KYCDocumentSerializer(docs, many=True, context={"request": request}).data,
            })
        return Response(result)


class AdminVerifyShopView(APIView):
    @admin_required
    def patch(self, request, shop_id):
        from shops.models import Shop, KYCDocument
        try:
            shop = Shop.objects.get(id=shop_id)
        except Shop.DoesNotExist:
            return Response({"detail": "Shop not found."}, status=404)
        action = request.data.get("action")  # "approve" | "reject"
        rejection_note = request.data.get("rejection_note", "")
        if action not in ("approve", "reject"):
            return Response({"detail": "action must be 'approve' or 'reject'."}, status=400)
        new_doc_status = "approved" if action == "approve" else "rejected"
        KYCDocument.objects.filter(shop=shop, status="pending").update(
            status=new_doc_status,
            rejection_note=rejection_note if action == "reject" else "",
            reviewed_at=timezone.now(),
        )
        if action == "approve":
            shop.status = "active"
            shop.is_verified = True
        else:
            shop.status = "rejected"
        shop.save()
        from shops.serializers import ShopSerializer
        return Response(ShopSerializer(shop).data)


class AdminDisputeListView(APIView):
    @admin_required
    def get(self, request):
        from disputes.models import Dispute
        from disputes.serializers import DisputeSerializer
        qs = Dispute.objects.all().order_by("-created_at")
        status_filter = request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return Response(DisputeSerializer(qs, many=True).data)


class AdminPayoutListView(APIView):
    @admin_required
    def get(self, request):
        from payments.models import Payout
        from payments.serializers import PayoutSerializer
        qs = Payout.objects.all().order_by("-payout_date")
        return Response(PayoutSerializer(qs, many=True).data)


class AdminCommissionsView(APIView):
    @admin_required
    def get(self, request):
        from orders.models import Order
        from django.db.models.functions import TruncMonth
        monthly = (
            Order.objects.filter(status="completed")
            .annotate(month=TruncMonth("placed_at"))
            .values("month")
            .annotate(
                gmv=Sum("total"),
                orders=Count("id"),
            )
            .order_by("-month")[:12]
        )
        # Approximate commission at 5% of GMV
        result = []
        for row in monthly:
            gmv = row["gmv"] or 0
            result.append({
                "month": row["month"].strftime("%b %Y") if row["month"] else "",
                "gmv": gmv,
                "revenue": int(gmv * 0.05),
                "orders": row["orders"],
                "rate": 5.0,
            })
        return Response(result)


class AdminHealthView(APIView):
    @admin_required
    def get(self, request):
        from django.db import connection
        # Basic health checks
        checks = []
        # DB
        try:
            connection.ensure_connection()
            checks.append({"service": "Database", "status": "ok", "latency_ms": 1})
        except Exception as e:
            checks.append({"service": "Database", "status": "error", "detail": str(e)})

        # Orders in last hour
        cutoff = timezone.now() - datetime.timedelta(hours=1)
        from orders.models import Order
        recent = Order.objects.filter(placed_at__gte=cutoff).count()
        checks.append({
            "service": "Order pipeline",
            "status": "ok",
            "detail": f"{recent} orders in last hour",
        })

        return Response({"checks": checks, "timestamp": timezone.now().isoformat()})


class AdminFraudSignalsView(APIView):
    @admin_required
    def get(self, request):
        from payments.models import Payment
        from django.db.models import Count as DCount
        # Users with multiple failed payments
        flagged = (
            Payment.objects.filter(status="failed")
            .values("order__buyer__username", "order__buyer__id")
            .annotate(failures=DCount("id"))
            .filter(failures__gte=3)
            .order_by("-failures")[:20]
        )
        return Response({
            "flagged_users": list(flagged),
        })


class AdminAgentKYCQueueView(APIView):
    """List agents with pending KYC documents."""
    @admin_required
    def get(self, request):
        from .models import AgentKYCDocument
        from .serializers import AgentKYCDocumentSerializer
        pending_docs = AgentKYCDocument.objects.filter(status="pending").select_related("agent").order_by("created_at")
        result = {}
        for doc in pending_docs:
            uid = doc.agent_id
            if uid not in result:
                result[uid] = {
                    "user_id": uid,
                    "username": doc.agent.username,
                    "email": doc.agent.email,
                    "full_name": doc.agent.get_full_name() or doc.agent.username,
                    "city": doc.agent.city,
                    "submitted_at": doc.created_at.isoformat(),
                    "documents": [],
                }
            result[uid]["documents"].append(
                AgentKYCDocumentSerializer(doc, context={"request": request}).data
            )
        return Response(list(result.values()))


class AdminVerifyAgentView(APIView):
    """Approve or reject an agent's KYC — updates is_kyc_verified on the user."""
    @admin_required
    def patch(self, request, user_id):
        from .models import AgentKYCDocument
        try:
            agent = User.objects.get(pk=user_id, role="agent")
        except User.DoesNotExist:
            return Response({"detail": "Agent not found."}, status=404)
        action = request.data.get("action")  # "approve" | "reject"
        rejection_note = request.data.get("rejection_note", "")
        if action not in ("approve", "reject"):
            return Response({"detail": "action must be 'approve' or 'reject'."}, status=400)
        new_status = "approved" if action == "approve" else "rejected"
        AgentKYCDocument.objects.filter(agent=agent, status="pending").update(
            status=new_status,
            rejection_note=rejection_note if action == "reject" else "",
            reviewed_at=timezone.now(),
        )
        if action == "approve":
            agent.is_kyc_verified = True
            agent.save(update_fields=["is_kyc_verified"])
        return Response(UserSerializer(agent).data)
