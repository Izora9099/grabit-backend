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
            last = Payment.objects.order_by("-id").first()
            next_num = (last.id + 1) if last else 1000
            self.payment_id = f"PAY-{next_num}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.payment_id


class Payout(models.Model):
    STATUS_CHOICES = [("processing", "Processing"), ("paid", "Paid"), ("failed", "Failed")]

    payout_id = models.CharField(max_length=20, unique=True)
    recipient = models.ForeignKey(User, on_delete=models.PROTECT, related_name="payouts")
    method = models.CharField(max_length=20)
    amount = models.PositiveIntegerField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="processing")
    payout_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-payout_date"]

    def save(self, *args, **kwargs):
        if not self.payout_id:
            last = Payout.objects.order_by("-id").first()
            next_num = (last.id + 1) if last else 1
            self.payout_id = f"PO-{next_num}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.payout_id


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
