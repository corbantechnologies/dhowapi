from rest_framework import serializers
from refund_log.models import RefundStatusLog


class RefundStatusLogSerializer(serializers.ModelSerializer):
    changed_by_email = serializers.ReadOnlyField(source="changed_by.email")
    refund_reference = serializers.ReadOnlyField(source="refund.reference")

    class Meta:
        model = RefundStatusLog
        fields = (
            "id",
            "refund",
            "refund_reference",
            "old_status",
            "new_status",
            "changed_by",
            "changed_by_email",
            "notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")
