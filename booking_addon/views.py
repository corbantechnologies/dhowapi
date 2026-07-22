from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from booking_addon.models import BookingAddOn
from booking_addon.serializers import BookingAddOnSerializer


class BookingAddOnListCreateView(generics.ListCreateAPIView):
    serializer_class = BookingAddOnSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["booking", "addon"]

    def get_queryset(self):
        user = self.request.user
        if user.is_dhow_manager or user.is_staff or user.is_superuser:
            return BookingAddOn.objects.all()
        return BookingAddOn.objects.filter(booking__booked_by=user)


class BookingAddOnDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BookingAddOnSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_dhow_manager or user.is_staff or user.is_superuser:
            return BookingAddOn.objects.all()
        return BookingAddOn.objects.filter(booking__booked_by=user)
