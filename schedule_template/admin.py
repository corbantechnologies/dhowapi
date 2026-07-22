from django.contrib import admin
from schedule_template.models import ScheduleTemplate


@admin.register(ScheduleTemplate)
class ScheduleTemplateAdmin(admin.ModelAdmin):
    list_display = (
        "dhow",
        "meal_type",
        "departure_time",
        "return_time",
        "price_per_person",
        "is_active",
        "reference",
    )
    list_filter = ("meal_type", "is_active", "dhow")
    search_fields = ("reference", "dhow__name")
