from django.contrib import admin
from escrow.models import EscrowRecord


@admin.register(EscrowRecord)
class EscrowRecordAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "payment",
        "schedule",
        "amount",
        "status",
        "resolution_method",
        "held_at",
        "resolved_at",
    )
    list_filter = ("status", "resolution_method")
    search_fields = ("reference", "payment__reference")
