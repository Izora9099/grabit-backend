from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import EscrowEvent, Order, Message
from .serializers import CreateOrderSerializer, OrderSerializer, MessageSerializer, ConversationSerializer, ReceiptSerializer
from .signals import order_status_changed


class OrderListCreateView(generics.ListCreateAPIView):
    def get_serializer_class(self):
        return CreateOrderSerializer if self.request.method == "POST" else OrderSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Order.objects.select_related(
            "shop", "shop__owner", "buyer", "agent"
        ).prefetch_related("items__product", "financials")
        if user.role == "vendor":
            try:
                return qs.filter(shop=user.shop)
            except Exception:
                return Order.objects.none()
        if user.role == "agent":
            return qs.filter(agent=user)
        return qs.filter(buyer=user)

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
        qs = Order.objects.select_related(
            "shop", "shop__owner", "buyer", "agent"
        ).prefetch_related("items__product", "financials")
        if user.role == "vendor":
            try:
                return qs.filter(shop=user.shop)
            except Exception:
                return Order.objects.none()
        if user.role == "agent":
            return qs.filter(agent=user)
        return qs.filter(buyer=user)


class OrderReceiptView(generics.RetrieveAPIView):
    """
    Returns a receipt-optimised payload for a single order.
    Includes payment details, buyer contact, and shop contact — everything the
    frontend needs to render or print a purchase receipt. Same BOLA scoping as
    OrderDetailView.
    """
    serializer_class = ReceiptSerializer
    lookup_field = "order_id"

    def get_queryset(self):
        user = self.request.user
        qs = Order.objects.select_related(
            "shop", "buyer", "agent"
        ).prefetch_related("items__product", "financials", "payment")
        if user.role == "vendor":
            try:
                return qs.filter(shop=user.shop)
            except AttributeError:
                return Order.objects.none()
        if user.role == "agent":
            return qs.filter(agent=user)
        if user.role == "admin":
            return qs
        return qs.filter(buyer=user)


class OrderStatusUpdateView(APIView):
    """Vendor or agent advances the order status.  Row-level lock prevents double-transitions."""
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
        role = request.user.role
        new_status = request.data.get("status")
        allowed = self.ALLOWED_TRANSITIONS.get(role, {})

        with transaction.atomic():
            # BOLA: scope the query to the requesting user's role so users cannot
            # transition orders that don't belong to them.
            if role == "vendor":
                order = get_object_or_404(
                    Order.objects.select_for_update(),
                    order_id=order_id, shop=request.user.shop,
                )
            elif role == "agent":
                order = get_object_or_404(
                    Order.objects.select_for_update(),
                    order_id=order_id, agent=request.user,
                )
            elif role == "buyer":
                order = get_object_or_404(
                    Order.objects.select_for_update(),
                    order_id=order_id, buyer=request.user,
                )
            else:
                return Response({"detail": "Transition not allowed."}, status=status.HTTP_400_BAD_REQUEST)

            if order.status not in allowed or allowed[order.status] != new_status:
                return Response({"detail": "Transition not allowed."}, status=status.HTTP_400_BAD_REQUEST)

            old_status = order.status
            order.status = new_status
            if new_status == "completed":
                order.escrow_released = True
                order.save()
                EscrowEvent.objects.create(
                    order=order,
                    event="released",
                    amount=order.total,
                    note="Buyer confirmed delivery. Escrow released to vendor.",
                )
            else:
                order.save()

        order_status_changed.send(
            sender=order.__class__,
            order=order,
            old_status=old_status,
            new_status=new_status,
            actor=request.user,
        )
        return Response(OrderSerializer(order).data)


class ConfirmDeliveryView(APIView):
    """Buyer confirms delivery → completes order and releases escrow."""
    def post(self, request, order_id):
        with transaction.atomic():
            order = get_object_or_404(
                Order.objects.select_for_update(),
                order_id=order_id, buyer=request.user,
            )
            if order.status != "delivered_confirm":
                return Response({"detail": "Order is not awaiting confirmation."}, status=400)
            order.status = "completed"
            order.escrow_released = True
            order.save()
            EscrowEvent.objects.create(
                order=order,
                event="released",
                amount=order.total,
                note="Buyer confirmed delivery. Escrow released to vendor.",
            )
        order_status_changed.send(
            sender=order.__class__,
            order=order,
            old_status="delivered_confirm",
            new_status="completed",
            actor=request.user,
        )
        return Response({"detail": "Order confirmed. Escrow released to vendor."})


class OrderCancelView(APIView):
    """Vendor cancels an order before it has been picked up."""
    def post(self, request, order_id):
        try:
            shop = request.user.shop
        except AttributeError:
            return Response({"detail": "Not found."}, status=404)

        with transaction.atomic():
            order = get_object_or_404(
                Order.objects.select_for_update(),
                order_id=order_id, shop=shop,
            )
            if order.status not in ("awaiting_payment", "paid_escrow", "preparing", "agent_assigned"):
                return Response({"detail": "Order cannot be cancelled at this stage."}, status=400)

            was_paid = order.status == "paid_escrow"
            old_status = order.status
            order.status = "cancelled"
            order.save()

            if was_paid:
                # Funds were in escrow — log that a refund is due so admin/payment processor can action it
                EscrowEvent.objects.create(
                    order=order,
                    event="refunded",
                    amount=order.total,
                    note="Vendor cancelled order after buyer payment. Refund due to buyer.",
                )

        order_status_changed.send(
            sender=order.__class__,
            order=order,
            old_status=old_status,
            new_status="cancelled",
            actor=request.user,
        )
        return Response(OrderSerializer(order).data)


class AgentDeclineView(APIView):
    """Agent declines an assigned delivery — order returns to preparing for reassignment."""
    def post(self, request, order_id):
        with transaction.atomic():
            order = get_object_or_404(
                Order.objects.select_for_update(),
                order_id=order_id, agent=request.user,
            )
            if order.status != "agent_assigned":
                return Response(
                    {"detail": "You can only decline orders in agent_assigned status."}, status=400
                )
            order.agent = None
            order.status = "preparing"
            order.save()

        return Response(OrderSerializer(order).data)


class MessageListCreateView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer

    def get_queryset(self):
        user = self.request.user
        return (
            Message.objects.filter(Q(sender=user) | Q(recipient=user))
            .select_related("sender", "recipient")
            .order_by("created_at")
        )

    def perform_create(self, serializer):
        user = self.request.user
        order = serializer.validated_data.get("order")
        recipient = serializer.validated_data["recipient"]

        if order:
            allowed_ids = {order.buyer_id, order.shop.owner_id}
            if order.agent_id:
                allowed_ids.add(order.agent_id)
            if user.id not in allowed_ids or recipient.id not in allowed_ids:
                raise PermissionDenied("You are not a participant in this order.")

        serializer.save(sender=user)


class MessageMarkReadView(APIView):
    """Mark a single message as read. Only the recipient can do this."""
    def patch(self, request, pk):
        message = get_object_or_404(Message, pk=pk, recipient=request.user)
        message.read = True
        message.save(update_fields=["read"])
        return Response(MessageSerializer(message).data)


class UnreadCountView(APIView):
    """Returns the total number of unread messages for the authenticated user."""
    def get(self, request):
        count = Message.objects.filter(recipient=request.user, read=False).count()
        return Response({"count": count})


class ConversationListView(APIView):
    """
    Lists all conversations for the authenticated user, grouped by the other
    participant. Each entry includes the last message and unread count.
    Sorted by most recent message first.
    """
    def get(self, request):
        user = request.user
        messages = (
            Message.objects.filter(Q(sender=user) | Q(recipient=user))
            .select_related("sender", "recipient")
            .order_by("created_at")
        )

        conversations = {}
        for msg in messages:
            other = msg.recipient if msg.sender_id == user.id else msg.sender
            if other.id not in conversations:
                avatar = other.avatar.url if other.avatar else None
                conversations[other.id] = {
                    "user_id": other.id,
                    "user_name": other.get_full_name() or other.username,
                    "user_avatar": avatar,
                    "last_message": msg.body,
                    "last_message_at": msg.created_at,
                    "unread_count": 0,
                }
            else:
                conversations[other.id]["last_message"] = msg.body
                conversations[other.id]["last_message_at"] = msg.created_at

            if not msg.read and msg.recipient_id == user.id:
                conversations[other.id]["unread_count"] += 1

        result = sorted(conversations.values(), key=lambda x: x["last_message_at"], reverse=True)
        return Response(ConversationSerializer(result, many=True).data)


class ConversationDetailView(generics.ListAPIView):
    """
    Full message thread between the authenticated user and another user.
    Automatically marks all unread messages in the thread as read.
    """
    serializer_class = MessageSerializer

    def get_queryset(self):
        user = self.request.user
        other_id = self.kwargs["user_id"]
        qs = Message.objects.filter(
            Q(sender=user, recipient_id=other_id) |
            Q(sender_id=other_id, recipient=user)
        ).select_related("sender", "recipient").order_by("created_at")

        # Mark incoming unread messages as read when the thread is opened
        qs.filter(recipient=user, read=False).update(read=True)
        return qs


class AgentOrdersView(generics.ListAPIView):
    """Agent sees their assigned deliveries."""
    serializer_class = OrderSerializer

    def get_queryset(self):
        user = self.request.user
        status_filter = self.request.query_params.get("status")
        qs = Order.objects.select_related(
            "shop", "shop__owner", "buyer", "agent"
        ).prefetch_related("items__product", "financials").filter(agent=user)
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


class AgentStatsView(APIView):
    """Aggregate stats for the authenticated agent."""
    def get(self, request):
        from django.utils import timezone
        from django.db.models import Sum
        import datetime

        user = request.user
        today = timezone.now().date()
        week_start = today - datetime.timedelta(days=today.weekday())

        deliveries = Order.objects.filter(agent=user)
        today_count = deliveries.filter(updated_at__date=today, status="completed").count()
        week_orders = deliveries.filter(updated_at__date__gte=week_start)

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
