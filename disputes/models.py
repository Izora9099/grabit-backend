from django.db import models
from accounts.models import User
from orders.models import Order


class Dispute(models.Model):
    REASON_CHOICES = [
        ("wrong_item", "Wrong item received"),
        ("damaged", "Damaged on arrival"),
        ("not_delivered", "Item never delivered"),
        ("not_as_described", "Not as described"),
        ("counterfeit", "Counterfeit suspected"),
    ]
    STATUS_CHOICES = [
        ("open", "Open"), ("urgent", "Urgent"),
        ("in_review", "In review"), ("resolved", "Resolved"),
    ]
    RESOLUTION_CHOICES = [
        ("refund_buyer", "Full refund to buyer"),
        ("release_vendor", "Release to vendor"),
        ("partial_refund", "Partial refund"),
    ]

    dispute_id = models.CharField(max_length=20, unique=True)
    order = models.OneToOneField(Order, on_delete=models.PROTECT, related_name="dispute")
    opened_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="opened_disputes")
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    description = models.TextField()
    evidence = models.FileField(upload_to="disputes/evidence/", null=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="open")
    resolution = models.CharField(max_length=20, choices=RESOLUTION_CHOICES, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="resolved_disputes")
    admin_note = models.TextField(blank=True)
    buyer_refund_amount   = models.PositiveIntegerField(null=True, blank=True, help_text="Set on partial_refund resolution")
    vendor_release_amount = models.PositiveIntegerField(null=True, blank=True, help_text="Set on partial_refund resolution")
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.dispute_id

    def save(self, *args, **kwargs):
        if not self.dispute_id:
            from core.sequences import next_sequence_value
            self.dispute_id = f"DSP-{next_sequence_value('dispute_id_seq')}"
        super().save(*args, **kwargs)
