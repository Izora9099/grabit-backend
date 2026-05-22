from django.db import models
from accounts.models import User


class Notification(models.Model):
    TYPE_CHOICES = [
        ("order", "Order"), ("delivery", "Delivery"),
        ("price", "Price drop"), ("shop", "Shop"),
        ("dispute", "Dispute"), ("system", "System"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    body = models.TextField()
    href = models.CharField(max_length=200, blank=True)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
