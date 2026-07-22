from rest_framework import serializers
from escrow.models import EscrowRecord


class EscrowRecordSerializer(serializers.ModelSerializer):
    payment_reference = serializers.ReadOnlyField(source="payment.reference")
    booking_reference = serializers.ReadOnlyField(source="payment.booking.reference")
    schedule_date = serializers.ReadOnlyField(source="schedule.date")
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = EscrowRecord
        fields = (
            "id",
            "reference",
            "payment",
            "payment_reference",
            "booking_reference",
            "schedule",
            "schedule_date",
            "amount",
            "status",
            "status_display",
            "held_at",
            "resolved_at",
            "resolution_method",
            "notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "reference", "held_at", "created_at", "updated_at")
