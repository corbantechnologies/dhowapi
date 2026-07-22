from django.contrib import admin
from payment.models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "booking",
        "amount",
        "payment_method",
        "status",
        "receipt_number",
        "paid_by",
        "created_at",
    )
    list_filter = ("status", "payment_method")
    search_fields = ("reference", "receipt_number", "transaction_ref", "paid_by__email")
