from rest_framework import serializers
from booking_guest.models import BookingGuest


class BookingGuestSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingGuest
        fields = (
            "id",
            "booking",
            "first_name",
            "last_name",
            "email",
            "phone",
            "dietary_needs",
            "is_primary",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")
