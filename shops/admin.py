from django.contrib import admin
from .models import Shop, KYCDocument

@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ["name", "handle", "city", "status", "is_verified", "plan"]
    list_filter = ["status", "is_verified", "plan"]

@admin.register(KYCDocument)
class KYCAdmin(admin.ModelAdmin):
    list_display = ["shop", "doc_type", "label", "status"]
    list_filter = ["status", "doc_type"]
