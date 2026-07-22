from rest_framework import serializers
from table.models import Table


class TableSerializer(serializers.ModelSerializer):
    booking_reference = serializers.ReadOnlyField(source="assigned_to.reference")

    class Meta:
        model = Table
        fields = (
            "id",
            "schedule",
            "table_number",
            "capacity",
            "description",
            "is_available",
            "assigned_to",
            "booking_reference",
            "notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")
