from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from booking_status_log.models import BookingStatusLog
from booking_status_log.serializers import BookingStatusLogSerializer


class BookingStatusLogListCreateView(generics.ListCreateAPIView):
    serializer_class = BookingStatusLogSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["booking", "old_status", "new_status"]

    def get_queryset(self):
        user = self.request.user
        if user.is_dhow_manager or user.is_staff or user.is_superuser:
            return BookingStatusLog.objects.all()
        return BookingStatusLog.objects.filter(booking__booked_by=user)


class BookingStatusLogDetailView(generics.RetrieveAPIView):
    serializer_class = BookingStatusLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_dhow_manager or user.is_staff or user.is_superuser:
            return BookingStatusLog.objects.all()
        return BookingStatusLog.objects.filter(booking__booked_by=user)
