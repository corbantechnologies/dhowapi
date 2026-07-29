from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from accounts.permissions import IsOwnerOrDhowManager, IsDhowManager
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
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrDhowManager]
    lookup_field = "reference"


class BookingCancelView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrDhowManager]

    def patch(self, request, reference):
        booking = get_object_or_404(Booking, reference=reference)
        self.check_object_permissions(request, booking)

        old_status = booking.status
        booking.status = "cancelled"
        booking.save()

        # Log status change
        try:
            from booking_status_log.models import BookingStatusLog
            BookingStatusLog.objects.create(
                booking=booking,
                old_status=old_status,
                new_status="cancelled",
                changed_by=request.user,
                notes=request.data.get("notes", "Booking cancelled by user/manager"),
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

