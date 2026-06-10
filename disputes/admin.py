from django.contrib import admin
from .models import Dispute


@admin.register(Dispute)
class DisputeAdmin(admin.ModelAdmin):
    list_display = ["dispute_id", "order", "reason", "status", "created_at"]
    list_filter = ["status", "reason"]
