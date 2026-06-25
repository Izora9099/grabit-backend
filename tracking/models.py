from django.db import models
from orders.models import Order


class AgentLocation(models.Model):
    """Last known GPS position for an agent on an active order.

    Updated on every accepted push from the agent's WebSocket connection.
    Sent to late-joining viewers on connect so they see the latest position
    immediately rather than waiting for the next agent push.
    """
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="agent_location")
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    lng = models.DecimalField(max_digits=9, decimal_places=6)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.order.order_id} — ({self.lat}, {self.lng})"
