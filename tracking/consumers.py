import json
import time

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone

# Statuses where location tracking is meaningful
_TRACKABLE = {"agent_assigned", "picked_up", "in_transit", "delivered_confirm"}

# Minimum seconds between accepted location pushes per connection
_MIN_INTERVAL = 3


class TrackingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.order_id = self.scope["url_route"]["kwargs"]["order_id"]
        self.group_name = f"tracking_{self.order_id}"
        self._last_push = 0.0

        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        order = await _get_order(self.order_id)
        if order is None:
            await self.close(code=4004)
            return

        if not await _is_authorized(user, order):
            await self.close(code=4003)
            return

        self._user = user
        self._order = order

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Send last known position immediately so late joiners aren't staring at
        # an empty map while waiting for the next agent push.
        loc = await _get_last_location(order)
        if loc:
            await self.send(text_data=json.dumps({
                "type": "location.update",
                "lat": float(loc.lat),
                "lng": float(loc.lng),
                "timestamp": loc.updated_at.isoformat(),
            }))

    async def disconnect(self, close_code):
        if not hasattr(self, "group_name"):
            return
        if hasattr(self, "_user") and self._user.role == "agent":
            await self.channel_layer.group_send(
                self.group_name, {"type": "agent.offline"}
            )
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        # Only the assigned agent may push location updates.
        if not hasattr(self, "_user") or self._user.role != "agent":
            return

        # Server-side rate limit: drop updates faster than _MIN_INTERVAL seconds.
        now = time.monotonic()
        if now - self._last_push < _MIN_INTERVAL:
            return
        self._last_push = now

        try:
            data = json.loads(text_data)
            lat = float(data["lat"])
            lng = float(data["lng"])
        except (KeyError, ValueError, TypeError, json.JSONDecodeError):
            return

        # Reject coordinates outside valid WGS-84 ranges.
        if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lng <= 180.0):
            return

        await _upsert_location(self._order, lat, lng)

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "location.update",
                "lat": lat,
                "lng": lng,
                "timestamp": timezone.now().isoformat(),
                "agent_id": self._user.id,
            },
        )

    # ── Channel-layer message handlers ────────────────────────────────────────

    async def location_update(self, event):
        await self.send(text_data=json.dumps({
            "type": "location.update",
            "lat": event["lat"],
            "lng": event["lng"],
            "timestamp": event["timestamp"],
        }))

    async def agent_offline(self, event):
        await self.send(text_data=json.dumps({"type": "agent.offline"}))


# ── DB helpers (sync → async) ─────────────────────────────────────────────────

@database_sync_to_async
def _get_order(order_id: str):
    from orders.models import Order
    try:
        return Order.objects.select_related("buyer", "shop__owner", "agent").get(
            order_id=order_id
        )
    except Order.DoesNotExist:
        return None


@database_sync_to_async
def _is_authorized(user, order) -> bool:
    if user.role == "admin":
        return True
    if user.role == "buyer" and order.buyer_id == user.id:
        return True
    if user.role == "vendor" and order.shop.owner_id == user.id:
        return True
    if user.role == "agent" and order.agent_id == user.id:
        return True
    return False


@database_sync_to_async
def _get_last_location(order):
    from tracking.models import AgentLocation
    try:
        return AgentLocation.objects.get(order=order)
    except AgentLocation.DoesNotExist:
        return None


@database_sync_to_async
def _upsert_location(order, lat: float, lng: float):
    from tracking.models import AgentLocation
    AgentLocation.objects.update_or_create(
        order=order,
        defaults={"lat": lat, "lng": lng},
    )
