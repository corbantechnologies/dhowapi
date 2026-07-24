from django.contrib import admin
from booking_addon.models import BookingAddOn


@admin.register(BookingAddOn)
class BookingAddOnAdmin(admin.ModelAdmin):
    list_display = ("addon", "booking", "quantity", "unit_price", "total_price")
    list_filter = ("addon",)
    search_fields = ("booking__reference", "addon__name")
