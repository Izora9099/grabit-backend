from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ("buyer", "Buyer"),
        ("vendor", "Vendor"),
        ("agent", "Agent"),
        ("admin", "Admin"),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="buyer")
    phone = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=80, blank=True)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    is_kyc_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username} ({self.role})"


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
