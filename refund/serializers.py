from rest_framework import serializers
from refund.models import Refund


class RefundSerializer(serializers.ModelSerializer):
    payment_reference = serializers.ReadOnlyField(source="payment.reference")
    booking_reference = serializers.ReadOnlyField(source="booking.reference")
    requested_by_email = serializers.ReadOnlyField(source="requested_by.email")
    processed_by_email = serializers.ReadOnlyField(source="processed_by.email")
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    reason_display = serializers.CharField(source="get_reason_display", read_only=True)

    class Meta:
        model = Refund
        fields = (
            "id",
            "reference",
            "payment",
            "payment_reference",
            "booking",
            "booking_reference",
            "escrow",
            "amount",
            "reason",
            "reason_display",
            "status",
            "status_display",
            "requested_by",
            "requested_by_email",
            "processed_by",
            "processed_by_email",
            "requested_at",
            "processed_at",
            "mpesa_ref",
            "notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "reference", "requested_at", "created_at", "updated_at")
