from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from booking_guest.models import BookingGuest
from booking_guest.serializers import BookingGuestSerializer


class BookingGuestListCreateView(generics.ListCreateAPIView):
    serializer_class = BookingGuestSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["booking", "is_primary"]
    search_fields = ["first_name", "last_name", "email", "phone"]

    def get_queryset(self):
        user = self.request.user
        if user.is_dhow_manager or user.is_staff or user.is_superuser:
            return BookingGuest.objects.all()
        return BookingGuest.objects.filter(booking__booked_by=user)


class BookingGuestDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BookingGuestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_dhow_manager or user.is_staff or user.is_superuser:
            return BookingGuest.objects.all()
        return BookingGuest.objects.filter(booking__booked_by=user)
