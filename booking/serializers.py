import datetime
from rest_framework import serializers
from booking.models import Booking
from booking_guest.serializers import BookingGuestSerializer


class BookingSerializer(serializers.ModelSerializer):
    booked_by_email = serializers.SerializerMethodField()
    booked_by_name = serializers.SerializerMethodField()
    booking_guests = BookingGuestSerializer(many=True, read_only=True)
    schedule_date = serializers.ReadOnlyField(source="schedule.date")
    schedule_meal_type = serializers.ReadOnlyField(source="schedule.get_meal_type_display")
    package_name = serializers.ReadOnlyField(source="package.name")
    table_number = serializers.SerializerMethodField()
    total_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )

    # Optional nested guest fields for bulk walk-in/creation optimization
    primary_guest_name = serializers.CharField(write_only=True, required=False)
    primary_guest_email = serializers.EmailField(write_only=True, required=False, allow_blank=True, allow_null=True)
    primary_guest_phone = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)

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
            "adult_count",
            "child_count",
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
            "booking_guests",
            "primary_guest_name",
            "primary_guest_email",
            "primary_guest_phone",
            "created_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "reference", "created_by", "created_at", "updated_at")
        extra_kwargs = {
            "booked_by": {"required": False, "allow_null": True},
        }

    def create(self, validated_data):
        primary_name = validated_data.pop("primary_guest_name", "")
        primary_email = validated_data.pop("primary_guest_email", "")
        primary_phone = validated_data.pop("primary_guest_phone", "")

        booking = Booking(**validated_data)
        booking._primary_guest_name = primary_name
        booking._primary_guest_email = primary_email
        booking._primary_guest_phone = primary_phone
        booking.save()

        return booking

    def validate(self, attrs):
        schedule = attrs.get("schedule")
        adult_count = attrs.get("adult_count")
        child_count = attrs.get("child_count")
        if adult_count is not None or child_count is not None:
            ac = adult_count if adult_count is not None else 1
            cc = child_count if child_count is not None else 0
            attrs["party_size"] = ac + cc

        party_size = attrs.get("party_size", 1)
        is_exclusive = attrs.get("is_exclusive", False)

        if schedule:
            if schedule.date < datetime.date.today():
                raise serializers.ValidationError("Cannot book a sailing in the past.")
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

    def get_table_number(self, obj):
        tables = obj.assigned_tables.all()
        if tables.exists():
            return ", ".join([t.table_number for t in tables])
        return ""


