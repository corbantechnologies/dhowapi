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

    def validate(self, attrs):
        from django.db.models import Sum
        instance = self.instance
        schedule = attrs.get("schedule", instance.schedule if instance else None)
        capacity = attrs.get("capacity", instance.capacity if instance else 0)

        if schedule:
            dhow = schedule.dhow
            max_capacity = dhow.total_capacity
            
            existing_qs = Table.objects.filter(schedule=schedule)
            if instance:
                existing_qs = existing_qs.exclude(pk=instance.pk)
            existing_capacity = existing_qs.aggregate(total=Sum('capacity'))['total'] or 0

            if existing_capacity + capacity > max_capacity:
                raise serializers.ValidationError(
                    f"Total table capacity ({existing_capacity + capacity}) would exceed vessel capacity ({max_capacity})."
                )
        return attrs
