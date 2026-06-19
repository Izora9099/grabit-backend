from django.db import models
from accounts.models import User


class Shop(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("suspended", "Suspended"),
        ("under_review", "Under review"),
        ("rejected", "Rejected"),
    ]
    PLAN_CHOICES = [("starter", "Starter"), ("growth", "Growth"), ("premium", "Premium")]

    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name="shop")
    name = models.CharField(max_length=120)
    handle = models.SlugField(unique=True)
    tagline = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=80)
    city = models.CharField(max_length=80)
    neighbourhood = models.CharField(max_length=120, blank=True)
    logo = models.ImageField(upload_to="shops/logos/", null=True, blank=True)
    banner = models.ImageField(upload_to="shops/banners/", null=True, blank=True)
    accent_color = models.CharField(max_length=7, default="#16a34a")
    whatsapp = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    delivery_fee = models.PositiveIntegerField(default=0)
    free_shipping_threshold = models.PositiveIntegerField(default=0)
    return_policy = models.TextField(blank=True)
    processing_time = models.CharField(max_length=80, blank=True)
    plan = models.CharField(max_length=10, choices=PLAN_CHOICES, default="starter")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="active")
    is_verified = models.BooleanField(default=False)
    followers_count = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    reviews_count = models.PositiveIntegerField(default=0)
    response_time = models.CharField(max_length=40, blank=True)
    joined = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ShopFollow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="following")
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="followers")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "shop")


class ShopReview(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="shop_reviews")
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="shop_reviews")
    rating = models.PositiveSmallIntegerField()  # 1–5
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("shop", "buyer")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.buyer.get_full_name()} → {self.shop.name} ({self.rating}★)"


class KYCDocument(models.Model):
    STATUS_CHOICES = [("draft", "Draft"), ("pending", "Pending"), ("in_review", "In review"), ("approved", "Approved"), ("rejected", "Rejected"), ("not_submitted", "Not submitted")]
    TYPE_CHOICES = [("identity", "Identity"), ("address", "Address proof"), ("business", "Business registration")]

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="kyc_documents")
    doc_type = models.CharField(max_length=15, choices=TYPE_CHOICES)
    label = models.CharField(max_length=120)
    file = models.FileField(upload_to="kyc/", null=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="not_submitted")
    rejection_note = models.TextField(blank=True, default="")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.shop.name} — {self.label}"
