from rest_framework import serializers
from booking.models import Booking


class BookingSerializer(serializers.ModelSerializer):
    booked_by_email = serializers.SerializerMethodField()
    booked_by_name = serializers.SerializerMethodField()
    schedule_date = serializers.ReadOnlyField(source="schedule.date")
    schedule_meal_type = serializers.ReadOnlyField(source="schedule.get_meal_type_display")
    package_name = serializers.ReadOnlyField(source="package.name")
    table_number = serializers.ReadOnlyField(source="table.table_number")
    total_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )

    class Meta:
        model = Booking
        fields = (
            "id",
            "reference",
            "schedule",
            "schedule_date",
            "schedule_meal_type",
            "booked_by",
            "booked_by_email",
            "booked_by_name",
            "booking_type",
            "package",
            "package_name",
            "party_size",
            "status",
            "status_display",
            "cancellation_preference",
            "is_exclusive",
            "exclusive_note",
            "table_request",
            "special_requests",
            "internal_notes",
            "table",
            "table_number",
            "total_amount",
            "created_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "reference", "created_by", "created_at", "updated_at")
        extra_kwargs = {
            "booked_by": {"required": False, "allow_null": True},
        }

    def validate(self, attrs):
        schedule = attrs.get("schedule")
        party_size = attrs.get("party_size", 1)
        is_exclusive = attrs.get("is_exclusive", False)

        if schedule:
            if not schedule.is_open:
                raise serializers.ValidationError("Bookings are closed for this schedule.")
            if schedule.status in ["cancelled", "completed"]:
                raise serializers.ValidationError(
                    f"Cannot book a schedule that is {schedule.status}."
                )
            if schedule.is_exclusive:
                raise serializers.ValidationError(
                    "This schedule is already exclusively chartered."
                )
            if is_exclusive and schedule.bookings.filter(status__in=["pending", "confirmed"]).exists():
                raise serializers.ValidationError(
                    "Cannot book exclusively: this schedule already has existing bookings."
                )
            if not is_exclusive and schedule.available_capacity < party_size:
                raise serializers.ValidationError(
                    f"Requested party size ({party_size}) exceeds available capacity ({schedule.available_capacity})."
                )

        return attrs

    def get_booked_by_name(self, obj):
        primary_guest = obj.booking_guests.filter(is_primary=True).first()
        if primary_guest:
            return f"{primary_guest.first_name} {primary_guest.last_name}"
        return obj.booked_by.get_full_name() if obj.booked_by else ""

    def get_booked_by_email(self, obj):
        primary_guest = obj.booking_guests.filter(is_primary=True).first()
        if primary_guest and primary_guest.email:
            return primary_guest.email
        return obj.booked_by.email if obj.booked_by else ""
