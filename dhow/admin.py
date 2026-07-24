from django.contrib import admin
from dhow.models import Dhow


@admin.register(Dhow)
class DhowAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "reference",
        "total_capacity",
        "min_quota",
        "is_active",
        "is_available",
        "created_at",
    )
    list_filter = ("is_active", "is_available")
    search_fields = ("name", "reference")
