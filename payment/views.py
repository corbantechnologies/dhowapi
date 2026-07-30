from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.utils import timezone

from payment.models import Payment
from payment.serializers import PaymentSerializer, MpesaSTKInitiateSerializer
from payment.utils import initiate_mpesa_stk_push
from booking.models import Booking
from schedule.permissions import HasManifestAccessToken


class PaymentListCreateView(generics.ListCreateAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated | HasManifestAccessToken]
    filterset_fields = ["booking", "status", "payment_method"]
    search_fields = ["reference", "transaction_ref", "receipt_number", "phone_number"]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.is_dhow_manager or user.is_supervisor or user.is_staff or user.is_superuser:
                return Payment.objects.all()
            return Payment.objects.filter(paid_by=user)
        # Supervisor unauthenticated queryset
        schedule_ref = getattr(self.request, "manifest_schedule_ref", None)
        if schedule_ref:
            return Payment.objects.filter(booking__schedule__reference=schedule_ref)
        return Payment.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if user.is_authenticated:
            serializer.save(paid_by=user)
        else:
            schedule_ref = getattr(self.request, "manifest_schedule_ref", None)
            if not schedule_ref:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You do not have a valid manifest token.")
            
            booking = serializer.validated_data.get("booking")
            if booking.schedule.reference != schedule_ref:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({"booking": "You do not have permission to record payments for this booking."})
            
            serializer.save(paid_by=None)


class PaymentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "reference"

    def get_queryset(self):
        user = self.request.user
        if user.is_dhow_manager or user.is_supervisor or user.is_staff or user.is_superuser:
            return Payment.objects.all()
        return Payment.objects.filter(paid_by=user)


class MpesaSTKInitiateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = MpesaSTKInitiateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        booking_id = serializer.validated_data["booking_id"]
        phone_number = serializer.validated_data["phone_number"]
        booking = get_object_or_404(Booking, pk=booking_id)

        amount = booking.total_amount

        # Create or update pending payment record
        payment, _ = Payment.objects.get_or_create(
            booking=booking,
            status__in=["pending", "processing"],
            defaults={
                "amount": amount,
                "paid_by": request.user,
                "phone_number": phone_number,
                "payment_method": "mpesa",
                "status": "processing",
            },
        )
        payment.amount = amount
        payment.phone_number = phone_number
        payment.save()

        # Call Daraja STK Push API
        stk_res = initiate_mpesa_stk_push(
            phone_number=phone_number,
            amount=amount,
            reference=booking.reference,
            description=f"Dhow Booking {booking.reference}",
        )

        if stk_res.get("success"):
            payment.transaction_ref = stk_res.get("checkout_request_id")
            payment.status = "processing"
            payment.save()
            return Response(
                {
                    "message": "STK Push initiated successfully. Please enter your M-Pesa PIN on your phone.",
                    "payment_reference": payment.reference,
                    "checkout_request_id": payment.transaction_ref,
                },
                status=status.HTTP_200_OK,
            )
        else:
            payment.status = "failed"
            payment.notes = stk_res.get("message")
            payment.save()
            return Response(
                {"error": stk_res.get("message", "Failed to initiate STK push")},
                status=status.HTTP_400_BAD_REQUEST,
            )


class MpesaCallbackView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        stk_callback = data.get("Body", {}).get("stkCallback", {})
        result_code = stk_callback.get("ResultCode")
        checkout_request_id = stk_callback.get("CheckoutRequestID")

        try:
            payment = Payment.objects.get(transaction_ref=checkout_request_id)
        except Payment.DoesNotExist:
            return Response({"result": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)

        if result_code == 0:
            # Payment successful
            items = stk_callback.get("CallbackMetadata", {}).get("Item", [])
            receipt_number = None
            for item in items:
                if item.get("Name") == "MpesaReceiptNumber":
                    receipt_number = item.get("Value")

            payment.status = "completed"
            payment.receipt_number = receipt_number
            payment.paid_at = timezone.now()
            payment.save()

            # Confirm booking
            booking = payment.booking
            booking.status = "confirmed"
            booking.save()

            # Create Escrow record
            try:
                from escrow.models import EscrowRecord
                EscrowRecord.objects.get_or_create(
                    payment=payment,
                    defaults={
                        "schedule": booking.schedule,
                        "amount": payment.amount,
                        "status": "holding",
                        "held_at": timezone.now(),
                    },
                )
            except Exception as e:
                pass
        else:
            payment.status = "failed"
            payment.notes = stk_callback.get("ResultDesc", "Transaction failed")
            payment.save()

        return Response({"ResultCode": 0, "ResultDesc": "Accepted"}, status=status.HTTP_200_OK)
