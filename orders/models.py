from decimal import Decimal

from django.db import models
from accounts.models import User
from products.models import Product
from shops.models import Shop


def get_commission_rate(shop) -> Decimal:
    from payments.models import PlatformConfig  # late import: payments→orders exists at module level; this avoids circular at load time
    cfg = PlatformConfig.get()
    return {
        "starter": cfg.starter_commission,
        "growth":  cfg.growth_commission,
        "premium": cfg.premium_commission,
    }.get(shop.plan, cfg.growth_commission)


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
            from core.sequences import next_sequence_value
            self.order_id = f"GR-{next_sequence_value('order_id_seq')}"
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


class OrderFinancials(models.Model):
    """Immutable financial breakdown recorded at order creation time."""
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="financials")
    subtotal              = models.PositiveIntegerField(help_text="Sum of items before delivery fee, in XAF")
    delivery_fee          = models.PositiveIntegerField(default=0, help_text="Delivery fee charged, in XAF")
    total                 = models.PositiveIntegerField(help_text="subtotal + delivery_fee, in XAF")
    commission_rate       = models.DecimalField(max_digits=6, decimal_places=4, help_text="e.g. 0.0500 for 5%")
    platform_fee          = models.PositiveIntegerField(help_text="Platform commission, in XAF")
    seller_amount         = models.PositiveIntegerField(help_text="Amount owed to vendor after commission, in XAF")
    buyer_refund_amount   = models.PositiveIntegerField(null=True, blank=True, help_text="Populated on partial_refund resolution")
    vendor_release_amount = models.PositiveIntegerField(null=True, blank=True, help_text="Populated on partial_refund resolution")
    created_at            = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Financials for {self.order.order_id}"


class DeliveryReview(models.Model):
    """Buyer rating of the delivery agent for a specific completed order."""
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="delivery_review")
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name="delivery_reviews")
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="given_delivery_reviews")
    rating = models.PositiveSmallIntegerField()
    text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.buyer.username} → agent {self.agent.username} ({self.rating}★)"


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
