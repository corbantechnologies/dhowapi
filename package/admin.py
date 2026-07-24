from django.contrib import admin
from package.models import Package


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ("name", "reference", "meal_type", "base_price", "is_active", "created_at")
    list_filter = ("meal_type", "is_active")
    search_fields = ("name", "reference")
