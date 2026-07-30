from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404

from accounts.permissions import IsOwnerOrDhowManager, IsDhowManager
from schedule.permissions import HasManifestAccessToken
from booking.models import Booking
from booking.serializers import BookingSerializer


class BookingListCreateView(generics.ListCreateAPIView):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["schedule", "status", "booking_type", "cancellation_preference"]
    search_fields = ["reference", "booked_by__email", "booked_by__first_name", "booked_by__last_name"]

    def get_queryset(self):
        user = self.request.user
        if user.is_dhow_manager or user.is_staff or user.is_superuser:
            return Booking.objects.all()
        return Booking.objects.filter(booked_by=user)

    def perform_create(self, serializer):
        user = self.request.user
        if user.is_dhow_manager or user.is_staff or user.is_superuser:
            booked_by = serializer.validated_data.get("booked_by", None)
        else:
            booked_by = serializer.validated_data.get("booked_by", user)
        serializer.save(booked_by=booked_by, created_by=user)


class BookingDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated | HasManifestAccessToken]
    lookup_field = "reference"

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.is_dhow_manager or user.is_staff or user.is_superuser:
                return Booking.objects.all()
            return Booking.objects.filter(booked_by=user)
        # Unauthenticated access via manifest token — restrict to that schedule
        schedule_ref = getattr(self.request, "manifest_schedule_ref", None)
        if schedule_ref:
            return Booking.objects.filter(schedule__reference=schedule_ref)
        return Booking.objects.none()


class BookingCancelView(APIView):
    permission_classes = [IsAuthenticated | HasManifestAccessToken]

    def patch(self, request, reference):
        booking = get_object_or_404(Booking, reference=reference)

        # Object-level permission — check if the actor can touch this booking
        if request.user.is_authenticated:
            # Standard auth: must be the owner or a dhow manager
            perm = IsOwnerOrDhowManager()
            if not perm.has_object_permission(request, self, booking):
                return Response(
                    {"detail": "You do not have permission to cancel this booking."},
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            # Manifest token access: verify booking belongs to the token's schedule
            perm = HasManifestAccessToken()
            if not perm.has_object_permission(request, self, booking):
                return Response(
                    {"detail": "You do not have permission to cancel this booking."},
                    status=status.HTTP_403_FORBIDDEN
                )

        old_status = booking.status
        booking.status = "cancelled"
        booking.save()

        # Release table assignment if present
        if booking.table:
            try:
                booking.table.assigned_to = None
                booking.table.is_available = True
                booking.table.save()
            except Exception:
                pass

        # Auto-create refund requests if there are completed payments
        try:
            from refund.models import Refund
            from escrow.models import EscrowRecord
            
            completed_payments = booking.payments.filter(status="completed")
            for payment in completed_payments:
                # Calculate already refunded amount for this payment
                refunded_sum = sum(rf.amount for rf in payment.refunds.filter(status__in=["pending", "processing", "completed"]))
                remaining_refund = payment.amount - refunded_sum
                
                if remaining_refund > 0:
                    # Look for associated escrow record in holding
                    escrow = EscrowRecord.objects.filter(payment=payment, status="holding").first()
                    if escrow:
                        escrow.status = "reversed_to_guest"
                        escrow.resolution_method = "booking_cancelled"
                        escrow.save()
                        
                    Refund.objects.create(
                        payment=payment,
                        booking=booking,
                        escrow=escrow,
                        amount=remaining_refund,
                        reason="other",
                        status="pending",
                        requested_by=request.user if request.user.is_authenticated else None,
                        notes=f"Auto-created refund on manual booking cancellation. Original Ref: {payment.reference}"
                    )
        except Exception:
            pass


        # Log status change
        try:
            from booking_status_log.models import BookingStatusLog
            BookingStatusLog.objects.create(
                booking=booking,
                old_status=old_status,
                new_status="cancelled",
                changed_by=request.user if request.user.is_authenticated else None,
                notes=request.data.get("notes", "Booking cancelled by manager/supervisor"),
            )
        except ImportError:
            pass

        serializer = BookingSerializer(booking)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BookingNoShowView(APIView):
    """Mark a booking as no-show. Accessible by managers or via manifest token."""
    permission_classes = [IsAuthenticated | HasManifestAccessToken]

    def patch(self, request, reference):
        booking = get_object_or_404(Booking, reference=reference)

        if request.user.is_authenticated:
            perm = IsOwnerOrDhowManager()
            if not perm.has_object_permission(request, self, booking):
                return Response(
                    {"detail": "You do not have permission to update this booking."},
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            perm = HasManifestAccessToken()
            if not perm.has_object_permission(request, self, booking):
                return Response(
                    {"detail": "You do not have permission to update this booking."},
                    status=status.HTTP_403_FORBIDDEN
                )

        old_status = booking.status
        booking.status = "no_show"
        booking.save()

        try:
            from booking_status_log.models import BookingStatusLog
            BookingStatusLog.objects.create(
                booking=booking,
                old_status=old_status,
                new_status="no_show",
                changed_by=request.user if request.user.is_authenticated else None,
                notes=request.data.get("notes", "Marked no-show by manager/supervisor"),
            )
        except ImportError:
            pass

        serializer = BookingSerializer(booking)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BookingAssignTableView(APIView):
    permission_classes = [IsDhowManager]

    def patch(self, request, reference):
        booking = get_object_or_404(Booking, reference=reference)
        table_id = request.data.get("table_id")

        if table_id:
            from table.models import Table
            table = get_object_or_404(Table, pk=table_id)
            booking.table = table
            table.assigned_to = booking
            table.is_available = False
            table.save()
        else:
            if booking.table:
                booking.table.assigned_to = None
                booking.table.is_available = True
                booking.table.save()
            booking.table = None

        booking.save()
        serializer = BookingSerializer(booking)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BookingBulkCreateView(APIView):
    permission_classes = [IsAuthenticated, IsDhowManager]

    def post(self, request):
        from django.db import transaction
        from payment.models import Payment
        
        bookings_data = request.data.get("bookings", [])
        if not bookings_data or not isinstance(bookings_data, list):
            return Response(
                {"detail": "Please provide a non-empty 'bookings' list."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        created_bookings = []
        try:
            with transaction.atomic():
                for index, data in enumerate(bookings_data):
                    serializer = BookingSerializer(data=data, context={"request": request})
                    if not serializer.is_valid():
                        # Collect and structure the validation errors
                        err_msgs = []
                        for field, errors in serializer.errors.items():
                            err_msgs.append(f"{field}: {', '.join(errors) if isinstance(errors, list) else str(errors)}")
                        return Response(
                            {"detail": f"Row {index + 1} validation failed: {'; '.join(err_msgs)}"},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                        
                    # Save the booking (sets booked_by=None for walk-ins)
                    booking = serializer.save(booked_by=None, created_by=request.user)
                    
                    payment_method = data.get("payment_method")
                    is_partial_payment = data.get("is_partial_payment", False)
                    partial_paid_amount = data.get("partial_paid_amount", 0)
                    
                    if payment_method and payment_method != "unpaid":
                        pay_amount = float(partial_paid_amount) if is_partial_payment else float(booking.total_amount)
                        
                        notes = (
                            f"Walk-in partial deposit collected by manager via {payment_method.upper()}. "
                            f"Remaining balance: KES {(float(booking.total_amount) - pay_amount):,.2f}"
                            if is_partial_payment else
                            f"Walk-in payment collected by manager via {payment_method.upper()}"
                        )
                        
                        Payment.objects.create(
                            booking=booking,
                            amount=pay_amount,
                            payment_method=payment_method,
                            status="completed",
                            phone_number=data.get("primary_guest_phone") or None,
                            transaction_ref=data.get("transaction_ref") or None,
                            notes=notes
                        )
                        
                    created_bookings.append(booking)
            
            response_serializer = BookingSerializer(created_bookings, many=True)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {"detail": f"Failed to bulk register bookings: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BookingPublicTicketView(APIView):
    """
    Publicly accessible detail endpoint for retrieving guest boarding passes.
    Authorized implicitly by knowing the secure, unique booking reference code.
    Only returns non-sensitive guest fields to prevent data leaks.
    """
    permission_classes = [AllowAny]

    def get(self, request, reference):
        booking = get_object_or_404(Booking, reference=reference)
        
        # Build safe customer payload
        data = {
            "reference": booking.reference,
            "booked_by_name": booking.booked_by_name,
            "party_size": booking.party_size,
            "adult_count": booking.adult_count,
            "child_count": booking.child_count,
            "status": booking.status,
            "status_display": booking.get_status_display(),
            "schedule_date": booking.schedule.date.strftime("%Y-%m-%d") if booking.schedule.date else "",
            "schedule_meal_type": booking.schedule.get_meal_type_display(),
            "departure_time": booking.schedule.departure_time.strftime("%H:%M") if booking.schedule.departure_time else "",
            "return_time": booking.schedule.return_time.strftime("%H:%M") if booking.schedule.return_time else "",
            "dhow_name": booking.schedule.dhow.name if booking.schedule.dhow else "",
            "table_number": booking.table_number,
            "special_requests": booking.special_requests or "",
            "booking_guests": [
                {
                    "first_name": g.first_name,
                    "last_name": g.last_name,
                    "is_primary": g.is_primary,
                    "status": g.status
                }
                for g in booking.booking_guests.all()
            ],
            "booking_addons": [
                {
                    "addon_name": ba.addon.name,
                    "quantity": ba.quantity
                }
                for ba in booking.booking_addons.all()
            ]
        }
        return Response(data, status=status.HTTP_200_OK)

