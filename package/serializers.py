from rest_framework import serializers
from package.models import Package


class PackageSerializer(serializers.ModelSerializer):
    meal_type_display = serializers.CharField(
        source="get_meal_type_display", read_only=True
    )

    class Meta:
        model = Package
        fields = (
            "id",
            "reference",
            "name",
            "meal_type",
            "meal_type_display",
            "description",
            "includes",
            "base_price",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "reference", "created_at", "updated_at")
