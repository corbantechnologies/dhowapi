from django.contrib import admin
from booking.models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "schedule",
        "booked_by",
        "booking_type",
        "party_size",
        "status",
        "cancellation_preference",
        "table",
        "created_at",
    )
    list_filter = ("status", "booking_type", "cancellation_preference", "is_exclusive")
    search_fields = ("reference", "booked_by__email", "booked_by__first_name", "booked_by__last_name")
