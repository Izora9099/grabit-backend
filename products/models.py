from django.db import models
from shops.models import Shop


class Product(models.Model):
    CONDITION_CHOICES = [("new", "New"), ("like_new", "Like new"), ("used", "Used")]
    STATUS_CHOICES = [("live", "Live"), ("draft", "Draft"), ("out_of_stock", "Out of stock"), ("pending_review", "Pending review")]
    CATEGORY_CHOICES = [
        ("electronics", "Electronics"), ("fashion", "Fashion"),
        ("home", "Home"), ("food", "Food"), ("sports", "Sports"), ("beauty", "Beauty"),
    ]

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.PositiveIntegerField(help_text="Price in XAF")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES, default="new")
    stock = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="draft")
    is_premium = models.BooleanField(default=False)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    reviews_count = models.PositiveIntegerField(default=0)
    views = models.PositiveIntegerField(default=0)
    sales = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/")
    is_primary = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    buyer = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField()  # 1–5
    text = models.TextField()
    is_verified_purchase = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("product", "buyer")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.buyer.username} → {self.product.name} ({self.rating}★)"


class WishlistItem(models.Model):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="wishlist")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")
