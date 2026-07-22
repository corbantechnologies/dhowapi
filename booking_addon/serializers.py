from rest_framework import serializers
from booking_addon.models import BookingAddOn


class BookingAddOnSerializer(serializers.ModelSerializer):
    addon_name = serializers.ReadOnlyField(source="addon.name")
    total_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = BookingAddOn
        fields = (
            "id",
            "booking",
            "addon",
            "addon_name",
            "quantity",
            "unit_price",
            "total_price",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")
