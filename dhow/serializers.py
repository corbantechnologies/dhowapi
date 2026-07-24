from rest_framework import serializers
from dhow.models import Dhow


class DhowSerializer(serializers.ModelSerializer):
    created_by_email = serializers.ReadOnlyField(source="created_by.email")

    class Meta:
        model = Dhow
        fields = (
            "id",
            "reference",
            "name",
            "description",
            "total_capacity",
            "min_quota",
            "image",
            "is_active",
            "is_available",
            "created_by",
            "created_by_email",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "reference", "created_by", "created_at", "updated_at")
