from django.contrib import admin
from .models import Product, ProductImage, Review


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ["image", "is_primary", "order"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "shop", "price", "category", "status", "stock"]
    list_filter = ["status", "category", "condition"]
    inlines = [ProductImageInline]

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["product", "buyer", "rating", "created_at"]
