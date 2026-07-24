from rest_framework import serializers
from booking_reschedule.models import BookingReschedule


class BookingRescheduleSerializer(serializers.ModelSerializer):
    booking_reference = serializers.ReadOnlyField(source="booking.reference")
    original_schedule_date = serializers.ReadOnlyField(source="original_schedule.date")
    new_schedule_date = serializers.ReadOnlyField(source="new_schedule.date")
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = BookingReschedule
        fields = (
            "id",
            "reference",
            "booking",
            "booking_reference",
            "original_schedule",
            "original_schedule_date",
            "new_schedule",
            "new_schedule_date",
            "reason",
            "rescheduled_by",
            "status",
            "status_display",
            "notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "reference", "created_at", "updated_at")
