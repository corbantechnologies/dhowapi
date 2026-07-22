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
        # If user is guest/agent, booked_by is self. If manager doing walk-in, booked_by can be passed or default to self.
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
