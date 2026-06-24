from decimal import Decimal

from django.db import models
from accounts.models import User
from orders.models import Order


class Payment(models.Model):
    METHOD_CHOICES = [
        ("mtn_momo", "MTN Mobile Money"),
        ("orange_money", "Orange Money"),
        ("bank_transfer", "Bank Transfer"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending"), ("processing", "Processing"),
        ("paid", "Paid"), ("failed", "Failed"), ("refunded", "Refunded"),
    ]

    payment_id = models.CharField(max_length=20, unique=True)
    order = models.OneToOneField(Order, on_delete=models.PROTECT, related_name="payment")
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    amount = models.PositiveIntegerField(help_text="Amount in XAF")
    phone_number = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="pending")
    external_ref = models.CharField(max_length=100, blank=True, help_text="MoMo/Orange transaction ref")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.payment_id:
            from core.sequences import next_sequence_value
            self.payment_id = f"PAY-{next_sequence_value('payment_id_seq')}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.payment_id


class Payout(models.Model):
    STATUS_CHOICES = [("processing", "Processing"), ("paid", "Paid"), ("failed", "Failed")]

    payout_id = models.CharField(max_length=20, unique=True)
    recipient = models.ForeignKey(User, on_delete=models.PROTECT, related_name="payouts")
    method = models.CharField(max_length=20)
    phone_number = models.CharField(max_length=20, blank=True)
    amount = models.PositiveIntegerField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="processing")
    payout_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-payout_date"]

    def save(self, *args, **kwargs):
        if not self.payout_id:
            from core.sequences import next_sequence_value
            self.payout_id = f"PO-{next_sequence_value('payout_id_seq')}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.payout_id


class PlatformConfig(models.Model):
    """
    Singleton (pk=1 only). Holds all live-adjustable platform parameters so the
    admin dashboard can change them without a code deploy.
    """
    starter_commission          = models.DecimalField(max_digits=6, decimal_places=4, default=Decimal("0.07"))
    growth_commission           = models.DecimalField(max_digits=6, decimal_places=4, default=Decimal("0.05"))
    premium_commission          = models.DecimalField(max_digits=6, decimal_places=4, default=Decimal("0.04"))
    escrow_release_hours        = models.PositiveIntegerField(default=72)
    dispute_window_hours        = models.PositiveIntegerField(default=48)
    free_shop_max_products      = models.PositiveIntegerField(default=20)
    premium_shop_max_products   = models.PositiveIntegerField(default=500)
    max_images_per_listing      = models.PositiveIntegerField(default=8)
    updated_at                  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Platform configuration"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class ProcessedWebhook(models.Model):
    """
    Idempotency guard for incoming Fapshi webhook events.
    A row is inserted before processing begins; duplicate transIds are rejected.
    """
    trans_id = models.CharField(max_length=200, unique=True)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["trans_id"])]

    def __str__(self):
        return self.trans_id
