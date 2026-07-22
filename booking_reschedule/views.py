from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from booking_reschedule.models import BookingReschedule
from booking_reschedule.serializers import BookingRescheduleSerializer


class BookingRescheduleListCreateView(generics.ListCreateAPIView):
    serializer_class = BookingRescheduleSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["booking", "status", "original_schedule", "new_schedule"]
    search_fields = ["reference", "booking__reference"]

    def get_queryset(self):
        user = self.request.user
        if user.is_dhow_manager or user.is_staff or user.is_superuser:
            return BookingReschedule.objects.all()
        return BookingReschedule.objects.filter(booking__booked_by=user)

    def perform_create(self, serializer):
        serializer.save(rescheduled_by=self.request.user)


class BookingRescheduleDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BookingRescheduleSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "reference"

    def get_queryset(self):
        user = self.request.user
        if user.is_dhow_manager or user.is_staff or user.is_superuser:
            return BookingReschedule.objects.all()
        return BookingReschedule.objects.filter(booking__booked_by=user)


class BookingRescheduleConfirmView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, reference):
        reschedule = get_object_or_404(BookingReschedule, reference=reference)
        new_schedule_id = request.data.get("new_schedule_id")

        if new_schedule_id:
            from schedule.models import Schedule
            new_sched = get_object_or_404(Schedule, pk=new_schedule_id)
            reschedule.new_schedule = new_sched

        if not reschedule.new_schedule:
            return Response(
                {"error": "Please provide a valid new_schedule_id to confirm reschedule."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reschedule.status = "confirmed"
        reschedule.save()

        # Move booking to new schedule
        booking = reschedule.booking
        booking.schedule = reschedule.new_schedule
        booking.status = "confirmed"
        booking.table = None  # Reset table assignment for manager to re-assign on new schedule
        booking.save()

        serializer = BookingRescheduleSerializer(reschedule)
        return Response(serializer.data, status=status.HTTP_200_OK)
