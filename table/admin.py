from django.contrib import admin
from table.models import Table


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ("table_number", "schedule", "capacity", "is_available", "assigned_to")
    list_filter = ("is_available", "schedule")
    search_fields = ("table_number", "description")
