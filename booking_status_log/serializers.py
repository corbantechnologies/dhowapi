from rest_framework import serializers
from booking_status_log.models import BookingStatusLog


class BookingStatusLogSerializer(serializers.ModelSerializer):
    changed_by_email = serializers.ReadOnlyField(source="changed_by.email")
    booking_reference = serializers.ReadOnlyField(source="booking.reference")

    class Meta:
        model = BookingStatusLog
        fields = (
            "id",
            "booking",
            "booking_reference",
            "old_status",
            "new_status",
            "changed_by",
            "changed_by_email",
            "notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")
