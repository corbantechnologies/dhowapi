from django.contrib import admin
from addon.models import AddOn


@admin.register(AddOn)
class AddOnAdmin(admin.ModelAdmin):
    list_display = ("name", "reference", "price", "is_available", "created_at")
    list_filter = ("is_available",)
    search_fields = ("name", "reference")
