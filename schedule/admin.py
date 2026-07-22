from django.contrib import admin
from schedule.models import Schedule


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = (
        "dhow",
        "date",
        "meal_type",
        "status",
        "is_open",
        "is_exclusive",
        "price_per_person",
        "reference",
    )
    list_filter = ("status", "is_open", "is_exclusive", "meal_type", "dhow")
    search_fields = ("reference", "dhow__name", "date")
