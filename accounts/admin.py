from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Address


@admin.register(User)
class GrabUserAdmin(BaseUserAdmin):
    list_display = ["username", "email", "role", "city", "is_kyc_verified"]
    list_filter = ["role", "is_kyc_verified"]
    fieldsets = BaseUserAdmin.fieldsets + (
        ("GrabIT", {"fields": ("role", "phone", "city", "avatar", "is_kyc_verified")}),
    )


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ["user", "label", "city"]
