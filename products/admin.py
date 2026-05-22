from django.contrib import admin
from .models import Product, Review

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "shop", "price", "category", "status", "stock"]
    list_filter = ["status", "category", "condition"]

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["product", "buyer", "rating", "created_at"]
