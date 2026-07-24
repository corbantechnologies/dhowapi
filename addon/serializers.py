from rest_framework import serializers
from addon.models import AddOn


class AddOnSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddOn
        fields = (
            "id",
            "reference",
            "name",
            "description",
            "price",
            "is_available",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "reference", "created_at", "updated_at")
