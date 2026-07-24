from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone

from accounts.permissions import IsDhowManager
from refund.models import Refund
from refund.serializers import RefundSerializer


class RefundListCreateView(generics.ListCreateAPIView):
    serializer_class = RefundSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["booking", "status", "reason"]
    search_fields = ["reference", "booking__reference", "mpesa_ref"]

    def get_queryset(self):
        user = self.request.user
        if user.is_dhow_manager or user.is_staff or user.is_superuser:
            return Refund.objects.all()
        return Refund.objects.filter(booking__booked_by=user)

    def perform_create(self, serializer):
        serializer.save(requested_by=self.request.user)


class RefundDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RefundSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "reference"

    def get_queryset(self):
        user = self.request.user
        if user.is_dhow_manager or user.is_staff or user.is_superuser:
            return Refund.objects.all()
        return Refund.objects.filter(booking__booked_by=user)


class RefundProcessView(APIView):
    permission_classes = [IsDhowManager]

    def patch(self, request, reference):
        refund = get_object_or_404(Refund, reference=reference)
        status_choice = request.data.get("status")  # "completed" or "rejected"
        mpesa_ref = request.data.get("mpesa_ref")
        notes = request.data.get("notes")

        if status_choice not in ["completed", "rejected"]:
            return Response(
                {"error": "Status must be 'completed' or 'rejected'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_status = refund.status
        refund.status = status_choice
        refund.processed_by = request.user
        refund.processed_at = timezone.now()
        if mpesa_ref:
            refund.mpesa_ref = mpesa_ref
        if notes:
            refund.notes = notes
        refund.save()

        # Log status change
        try:
            from refund_log.models import RefundStatusLog
            RefundStatusLog.objects.create(
                refund=refund,
                old_status=old_status,
                new_status=status_choice,
                changed_by=request.user,
                notes=f"Processed by accounts: {notes or ''}",
            )
        except ImportError:
            pass

        serializer = RefundSerializer(refund)
        return Response(serializer.data, status=status.HTTP_200_OK)
