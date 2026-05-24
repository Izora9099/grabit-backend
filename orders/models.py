from django.db import models
from accounts.models import User
from products.models import Product
from shops.models import Shop


class Order(models.Model):
    STATUS_CHOICES = [
        ("awaiting_payment", "Awaiting payment"),
        ("paid_escrow", "Paid — escrow held"),
        ("preparing", "Preparing"),
        ("agent_assigned", "Agent assigned"),
        ("picked_up", "Picked up"),
        ("in_transit", "In transit"),
        ("delivered_confirm", "Delivered — confirm"),
        ("completed", "Completed"),
        ("disputed", "Disputed"),
        ("cancelled", "Cancelled"),
        ("refunded", "Refunded"),
        ("partially_resolved", "Partially resolved"),
    ]

    order_id = models.CharField(max_length=20, unique=True)  # e.g. GR-10231
    buyer = models.ForeignKey(User, on_delete=models.PROTECT, related_name="orders")
    shop = models.ForeignKey(Shop, on_delete=models.PROTECT, related_name="orders")
    agent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="deliveries")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="awaiting_payment")
    city = models.CharField(max_length=80)
    delivery_address = models.TextField()
    total = models.PositiveIntegerField(help_text="Total in XAF")
    escrow_released = models.BooleanField(default=False)
    placed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-placed_at"]

    def __str__(self):
        return self.order_id

    def save(self, *args, **kwargs):
        if not self.order_id:
            last = Order.objects.order_by("-id").first()
            next_num = (last.id + 1) if last else 10001
            self.order_id = f"GR-{next_num}"
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.PositiveIntegerField()

    @property
    def subtotal(self):
        return self.quantity * self.unit_price


class EscrowEvent(models.Model):
    """Tracks every state change on the escrow ledger for audit."""
    EVENT_CHOICES = [
        ("held", "Funds held"), ("released", "Funds released"),
        ("refunded", "Funds refunded"), ("partial_refund", "Partial refund"),
    ]
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="escrow_events")
    event = models.CharField(max_length=20, choices=EVENT_CHOICES)
    amount = models.PositiveIntegerField()
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Message(models.Model):
    """In-app messaging between buyer, vendor, agent, support."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="messages", null=True, blank=True)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_messages")
    body = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
