from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from accounts.permissions import IsDhowManagerOrReadOnly, IsDhowManager
from schedule.models import Schedule
from schedule.serializers import ScheduleSerializer


class ScheduleListCreateView(generics.ListCreateAPIView):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    permission_classes = [IsDhowManagerOrReadOnly]
    filterset_fields = ["dhow", "date", "meal_type", "status", "is_open", "is_exclusive"]
    search_fields = ["reference", "dhow__name"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ScheduleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    permission_classes = [IsDhowManagerOrReadOnly]
    lookup_field = "reference"


class ScheduleOpenView(APIView):
    permission_classes = [IsDhowManager]

    def patch(self, request, reference):
        schedule = get_object_or_404(Schedule, reference=reference)
        schedule.is_open = True
        schedule.save()
        serializer = ScheduleSerializer(schedule)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ScheduleCloseView(APIView):
    permission_classes = [IsDhowManager]

    def patch(self, request, reference):
        schedule = get_object_or_404(Schedule, reference=reference)
        schedule.is_open = False
        schedule.save()
        serializer = ScheduleSerializer(schedule)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ScheduleConfirmView(APIView):
    permission_classes = [IsDhowManager]

    def patch(self, request, reference):
        schedule = get_object_or_404(Schedule, reference=reference)
        schedule.status = "confirmed"
        schedule.save()

        # Trigger Escrow release if escrow app is imported/active
        try:
            from escrow.models import EscrowRecord
            escrows = EscrowRecord.objects.filter(schedule=schedule, status="holding")
            for escrow in escrows:
                escrow.status = "released_to_finance"
                escrow.resolution_method = "schedule_confirmed"
                escrow.save()
        except ImportError:
            pass

        serializer = ScheduleSerializer(schedule)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ScheduleCancelView(APIView):
    permission_classes = [IsDhowManager]

    def patch(self, request, reference):
        schedule = get_object_or_404(Schedule, reference=reference)
        reason = request.data.get("reason", "Cancelled by management")
        schedule.status = "cancelled"
        schedule.cancelled_reason = reason
        schedule.save()

        # Cancel all pending/confirmed bookings for this schedule
        schedule.bookings.filter(status__in=["pending", "confirmed"]).update(status="cancelled")

        # Release all seating tables for this sailing voyage schedule
        schedule.tables.update(assigned_to=None, is_available=True)

        # Trigger Escrow reversal / refund / reschedule creation for bookings
        try:
            from escrow.models import EscrowRecord
            from refund.models import Refund
            from booking_reschedule.models import BookingReschedule

            escrows = EscrowRecord.objects.filter(schedule=schedule, status="holding")
            for escrow in escrows:
                escrow.status = "reversed_to_guest"
                escrow.resolution_method = "schedule_cancelled"
                escrow.save()

                booking = escrow.payment.booking
                if booking.cancellation_preference == "refund":
                    Refund.objects.get_or_create(
                        payment=escrow.payment,
                        booking=booking,
                        escrow=escrow,
                        defaults={
                            "amount": escrow.amount,
                            "reason": "sailing_cancelled",
                            "status": "pending",
                            "requested_by": request.user,
                            "notes": f"Auto-created refund due to schedule cancellation ({reason})",
                        },
                    )
                elif booking.cancellation_preference == "reschedule":
                    BookingReschedule.objects.get_or_create(
                        booking=booking,
                        original_schedule=schedule,
                        defaults={
                            "reason": f"Auto-created reschedule request due to schedule cancellation ({reason})",
                            "rescheduled_by": request.user,
                            "status": "pending",
                        },
                    )
        except ImportError:
            pass

        serializer = ScheduleSerializer(schedule)
        return Response(serializer.data, status=status.HTTP_200_OK)
