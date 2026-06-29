from django.contrib import admin
from .models import AnalyticsEvent


@admin.register(AnalyticsEvent)
class AnalyticsEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "shop", "product", "user", "created_at")
    list_filter = ("event_type",)
    readonly_fields = ("event_type", "shop", "product", "user", "session_key", "created_at")
    ordering = ("-created_at",)
