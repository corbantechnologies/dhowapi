from rest_framework import serializers
from schedule.models import Schedule


class ScheduleSerializer(serializers.ModelSerializer):
    dhow_name = serializers.ReadOnlyField(source="dhow.name")
    meal_type_display = serializers.CharField(
        source="get_meal_type_display", read_only=True
    )
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )
    current_pax_count = serializers.IntegerField(read_only=True)
    is_quota_met = serializers.BooleanField(read_only=True)
    available_capacity = serializers.IntegerField(read_only=True)

    class Meta:
        model = Schedule
        fields = (
            "id",
            "reference",
            "dhow",
            "dhow_name",
            "template",
            "date",
            "meal_type",
            "meal_type_display",
            "departure_time",
            "return_time",
            "price_per_person",
            "price_per_child",
            "exclusive_flat_fee",
            "status",
            "status_display",
            "is_exclusive",
            "exclusive_booked_by",
            "is_open",
            "cancelled_reason",
            "notes",
            "current_pax_count",
            "is_quota_met",
            "available_capacity",
            "created_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "reference", "created_by", "created_at", "updated_at")
