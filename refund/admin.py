from django.contrib import admin
from refund.models import Refund


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "booking",
        "amount",
        "reason",
        "status",
        "mpesa_ref",
        "processed_by",
        "requested_at",
    )
    list_filter = ("status", "reason")
    search_fields = ("reference", "booking__reference", "mpesa_ref")
