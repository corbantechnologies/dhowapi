from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from refund_log.models import RefundStatusLog
from refund_log.serializers import RefundStatusLogSerializer


class RefundStatusLogListCreateView(generics.ListCreateAPIView):
    serializer_class = RefundStatusLogSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["refund", "old_status", "new_status"]

    def get_queryset(self):
        user = self.request.user
        if user.is_dhow_manager or user.is_staff or user.is_superuser:
            return RefundStatusLog.objects.all()
        return RefundStatusLog.objects.filter(refund__booking__booked_by=user)


class RefundStatusLogDetailView(generics.RetrieveAPIView):
    serializer_class = RefundStatusLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_dhow_manager or user.is_staff or user.is_superuser:
            return RefundStatusLog.objects.all()
        return RefundStatusLog.objects.filter(refund__booking__booked_by=user)
