from rest_framework import serializers
from payment.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    booking_reference = serializers.ReadOnlyField(source="booking.reference")
    paid_by_email = serializers.ReadOnlyField(source="paid_by.email")
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Payment
        fields = (
            "id",
            "reference",
            "booking",
            "booking_reference",
            "amount",
            "currency",
            "payment_method",
            "status",
            "status_display",
            "paid_by",
            "paid_by_email",
            "paid_at",
            "transaction_ref",
            "receipt_number",
            "phone_number",
            "notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "reference", "created_at", "updated_at")


class MpesaSTKInitiateSerializer(serializers.Serializer):
    booking_id = serializers.UUIDField(required=True)
    phone_number = serializers.CharField(max_length=20, required=True)
