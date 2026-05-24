from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Order, Message
from .serializers import CreateOrderSerializer, OrderSerializer, MessageSerializer


class OrderListCreateView(generics.ListCreateAPIView):
    def get_serializer_class(self):
        return CreateOrderSerializer if self.request.method == "POST" else OrderSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == "vendor":
            try:
                return Order.objects.filter(shop=user.shop)
            except Exception:
                return Order.objects.none()
        if user.role == "agent":
            return Order.objects.filter(agent=user)
        return Order.objects.filter(buyer=user)

    def create(self, request, *args, **kwargs):
        serializer = CreateOrderSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    lookup_field = "order_id"

    def get_queryset(self):
        user = self.request.user
        if user.role == "vendor":
            try:
                return Order.objects.filter(shop=user.shop)
            except Exception:
                return Order.objects.none()
        if user.role == "agent":
            return Order.objects.filter(agent=user)
        return Order.objects.filter(buyer=user)


class OrderStatusUpdateView(APIView):
    """Vendor or agent updates the order status."""
    ALLOWED_TRANSITIONS = {
        "vendor": {
            "paid_escrow": "preparing",
            "preparing": "agent_assigned",
        },
        "agent": {
            "agent_assigned": "picked_up",
            "picked_up": "in_transit",
            "in_transit": "delivered_confirm",
        },
        "buyer": {
            "delivered_confirm": "completed",
        },
    }

    def patch(self, request, order_id):
        order = Order.objects.get(order_id=order_id)
        role = request.user.role
        new_status = request.data.get("status")
        allowed = self.ALLOWED_TRANSITIONS.get(role, {})
        if order.status not in allowed or allowed[order.status] != new_status:
            return Response({"detail": "Transition not allowed."}, status=status.HTTP_400_BAD_REQUEST)
        order.status = new_status
        if new_status == "completed":
            order.escrow_released = True
        order.save()
        return Response(OrderSerializer(order).data)


class ConfirmDeliveryView(APIView):
    """Buyer confirms delivery → completes order and releases escrow."""
    def post(self, request, order_id):
        order = Order.objects.get(order_id=order_id, buyer=request.user)
        if order.status != "delivered_confirm":
            return Response({"detail": "Order is not awaiting confirmation."}, status=400)
        order.status = "completed"
        order.escrow_released = True
        order.save()
        return Response({"detail": "Order confirmed. Escrow released to vendor."})


class OrderCancelView(APIView):
    """Vendor cancels an order before it has been picked up."""
    def post(self, request, order_id):
        try:
            order = Order.objects.get(order_id=order_id, shop=request.user.shop)
        except (Order.DoesNotExist, AttributeError):
            return Response({"detail": "Not found."}, status=404)
        if order.status not in ("awaiting_payment", "paid_escrow", "preparing", "agent_assigned"):
            return Response({"detail": "Order cannot be cancelled at this stage."}, status=400)
        order.status = "cancelled"
        order.save()
        return Response(OrderSerializer(order).data)


class AgentDeclineView(APIView):
    """Agent declines an assigned delivery — order returns to preparing for reassignment."""
    def post(self, request, order_id):
        try:
            order = Order.objects.get(order_id=order_id, agent=request.user)
        except Order.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)
        if order.status != "agent_assigned":
            return Response({"detail": "You can only decline orders in agent_assigned status."}, status=400)
        order.agent = None
        order.status = "preparing"
        order.save()
        return Response(OrderSerializer(order).data)


class MessageListCreateView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer

    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(sender=user) | Message.objects.filter(recipient=user)

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)


class AgentOrdersView(generics.ListAPIView):
    """Agent sees their assigned deliveries."""
    serializer_class = OrderSerializer

    def get_queryset(self):
        user = self.request.user
        status_filter = self.request.query_params.get("status")
        qs = Order.objects.filter(agent=user)
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


class AgentStatsView(APIView):
    """Aggregate stats for the authenticated agent."""
    def get(self, request):
        from django.utils import timezone
        from django.db.models import Sum, Count
        import datetime

        user = request.user
        today = timezone.now().date()
        week_start = today - datetime.timedelta(days=today.weekday())

        deliveries = Order.objects.filter(agent=user)
        today_count = deliveries.filter(placed_at__date=today, status="completed").count()
        week_orders = deliveries.filter(placed_at__date__gte=week_start)

        # Derive earnings from payouts if available, else estimate from order totals
        from payments.models import Payout
        week_earnings = Payout.objects.filter(
            recipient=user, payout_date__gte=week_start
        ).aggregate(total=Sum("amount"))["total"] or 0

        return Response({
            "today_deliveries": today_count,
            "week_deliveries": week_orders.count(),
            "week_earnings": week_earnings,
            "active_assignments": deliveries.filter(
                status__in=["picked_up", "in_transit", "preparing"]
            ).count(),
        })
