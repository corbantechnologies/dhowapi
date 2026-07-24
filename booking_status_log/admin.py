from django.contrib import admin
from booking_status_log.models import BookingStatusLog


@admin.register(BookingStatusLog)
class BookingStatusLogAdmin(admin.ModelAdmin):
    list_display = ("booking", "old_status", "new_status", "changed_by", "created_at")
    list_filter = ("old_status", "new_status")
    search_fields = ("booking__reference", "changed_by__email")
