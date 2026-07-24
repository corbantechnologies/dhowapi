from django.contrib import admin
from booking_reschedule.models import BookingReschedule


@admin.register(BookingReschedule)
class BookingRescheduleAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "booking",
        "original_schedule",
        "new_schedule",
        "status",
        "rescheduled_by",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = ("reference", "booking__reference")
