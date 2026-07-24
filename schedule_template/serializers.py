from rest_framework import serializers
from schedule_template.models import ScheduleTemplate


class ScheduleTemplateSerializer(serializers.ModelSerializer):
    dhow_name = serializers.ReadOnlyField(source="dhow.name")
    meal_type_display = serializers.CharField(
        source="get_meal_type_display", read_only=True
    )

    class Meta:
        model = ScheduleTemplate
        fields = (
            "id",
            "reference",
            "dhow",
            "dhow_name",
            "meal_type",
            "meal_type_display",
            "departure_time",
            "return_time",
            "days_of_week",
            "price_per_person",
            "exclusive_flat_fee",
            "is_active",
            "notes",
            "created_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "reference", "created_by", "created_at", "updated_at")
