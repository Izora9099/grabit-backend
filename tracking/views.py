from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import Order
from .models import AgentLocation


class AgentLocationView(APIView):
    """HTTP fallback for clients that cannot maintain a WebSocket connection."""

    def get(self, request, order_id):
        try:
            order = Order.objects.select_related(
                "buyer", "shop__owner", "agent"
            ).get(order_id=order_id)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found."}, status=404)

        user = request.user
        is_authorized = (
            user.role == "admin"
            or (user.role == "buyer" and order.buyer_id == user.id)
            or (user.role == "vendor" and order.shop.owner_id == user.id)
            or (user.role == "agent" and order.agent_id == user.id)
        )
        if not is_authorized:
            return Response({"detail": "Not authorized."}, status=403)

        try:
            loc = AgentLocation.objects.get(order=order)
        except AgentLocation.DoesNotExist:
            return Response({"detail": "No location data yet."}, status=404)

        return Response({
            "lat": float(loc.lat),
            "lng": float(loc.lng),
            "updated_at": loc.updated_at.isoformat(),
            "order_id": order.order_id,
            "order_status": order.status,
        })
