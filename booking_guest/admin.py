from django.contrib import admin
from booking_guest.models import BookingGuest


@admin.register(BookingGuest)
class BookingGuestAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "booking", "email", "phone", "is_primary")
    list_filter = ("is_primary",)
    search_fields = ("first_name", "last_name", "email", "booking__reference")
