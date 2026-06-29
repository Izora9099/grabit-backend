from django.db import models


class AnalyticsEvent(models.Model):
    EVENT_CHOICES = [
        ("product_viewed",   "Product viewed"),
        ("shop_visited",     "Shop visited"),
        ("wishlist_added",   "Wishlist add"),
        ("order_placed",     "Order placed"),
        ("order_paid",       "Order paid"),
        ("order_completed",  "Order completed"),
    ]

    event_type  = models.CharField(max_length=20, choices=EVENT_CHOICES, db_index=True)
    shop        = models.ForeignKey("shops.Shop",       on_delete=models.CASCADE,  null=True, blank=True, related_name="analytics_events")
    product     = models.ForeignKey("products.Product", on_delete=models.SET_NULL, null=True, blank=True, related_name="analytics_events")
    user        = models.ForeignKey("accounts.User",    on_delete=models.SET_NULL, null=True, blank=True, related_name="analytics_events")
    session_key = models.CharField(max_length=64, blank=True, default="")
    created_at  = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["shop", "event_type", "created_at"]),
        ]

    def __str__(self):
        return f"{self.event_type} — {self.shop_id} — {self.created_at:%Y-%m-%d}"
