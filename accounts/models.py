from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ("buyer", "Buyer"),
        ("vendor", "Vendor"),
        ("agent", "Agent"),
        ("admin", "Admin"),
    ]
    DELIVERY_TYPE_CHOICES = [
        ("intra_city", "Intra-city (same city only)"),
        ("intercity", "Intercity (across cities)"),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="buyer")
    phone = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=80, blank=True)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    is_kyc_verified = models.BooleanField(default=False)
    is_available = models.BooleanField(default=False, help_text="Agent online/offline toggle.")
    delivery_type = models.CharField(
        max_length=12,
        choices=DELIVERY_TYPE_CHOICES,
        default="intra_city",
        help_text="For agents only: whether they deliver within one city or between cities.",
    )

    def __str__(self):
        return f"{self.username} ({self.role})"


class AgentKYCDocument(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("pending", "Pending"),
        ("in_review", "In review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]
    TYPE_CHOICES = [
        ("identity", "National ID / Passport"),
        ("driving_license", "Driving license"),
        ("vehicle", "Vehicle registration"),
        ("address", "Address proof"),
    ]

    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name="agent_kyc_documents")
    doc_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    label = models.CharField(max_length=120)
    file = models.FileField(upload_to="agent_kyc/", null=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="draft")
    rejection_note = models.TextField(blank=True, default="")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.agent.username} — {self.label}"


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    label = models.CharField(max_length=40)
    line = models.CharField(max_length=200)
    city = models.CharField(max_length=80)
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_primary"]

    def __str__(self):
        return f"{self.label} — {self.user.username}"
