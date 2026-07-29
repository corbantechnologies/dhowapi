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


class SchedulePublicManifestView(APIView):
    permission_classes = []  # Public endpoint

    def get(self, request, reference):
        schedule = get_object_or_404(Schedule, reference=reference)

        # Get all confirmed or completed bookings for this schedule
        bookings = schedule.bookings.filter(
            status__in=["confirmed", "completed", "pending", "no_show"]
        ).order_by("created_at")

        # Format manifest records
        manifest_data = []
        for b in bookings:
            # Get table numbers
            tables = b.assigned_tables.all()
            table_numbers = ", ".join([t.table_number for t in tables]) if tables.exists() else ""

            # Get guests details
            guests_data = []
            for g in b.booking_guests.all().order_by("id"):
                guests_data.append({
                    "id": g.id,
                    "first_name": g.first_name,
                    "last_name": g.last_name,
                    "email": g.email or "",
                    "phone": g.phone or "",
                    "is_primary": g.is_primary,
                    "status": g.status,
                })

            primary_guest = b.booking_guests.filter(is_primary=True).first()
            if primary_guest:
                booked_by_name = f"{primary_guest.first_name} {primary_guest.last_name}"
            elif b.booked_by:
                booked_by_name = b.booked_by.get_full_name() or b.booked_by.username
            else:
                booked_by_name = "Walk-In Guest"

            manifest_data.append({
                "id": b.id,
                "reference": b.reference,
                "booked_by_name": booked_by_name,
                "party_size": b.party_size,
                "adult_count": b.adult_count,
                "child_count": b.child_count,
                "table_number": table_numbers,
                "special_requests": b.special_requests or "",
                "status": b.status,
                "booking_guests": guests_data,
            })

        data = {
            "schedule": {
                "reference": schedule.reference,
                "dhow_name": schedule.dhow.name,
                "date": str(schedule.date),
                "meal_type_display": schedule.get_meal_type_display(),
                "departure_time": str(schedule.departure_time),
                "return_time": str(schedule.return_time),
                "status": schedule.status,
            },
            "manifest": manifest_data
        }
        return Response(data, status=status.HTTP_200_OK)


class SchedulePDFDownloadView(APIView):
    permission_classes = []  # Public download link

    def get(self, request, reference):
        from django.http import HttpResponse
        from decouple import config
        from playwright.sync_api import sync_playwright

        schedule = get_object_or_404(Schedule, reference=reference)

        # Get front-end DOMAIN or default to localhost
        frontend_domain = config("DOMAIN", default="http://localhost:3000")
        manifest_url = f"{frontend_domain}/manifest/{reference}"

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-setuid-sandbox"]
                )
                page = browser.new_page()
                page.goto(manifest_url, wait_until="networkidle")
                
                # Wait for loading to finish and print button to render
                page.wait_for_selector('button:has-text("Print Manifest")', timeout=10000)
                
                pdf_bytes = page.pdf(
                    format="A4",
                    print_background=True,
                    margin={"top": "0.4in", "right": "0.4in", "bottom": "0.4in", "left": "0.4in"}
                )
                browser.close()

            response = HttpResponse(pdf_bytes, content_type="application/pdf")
            response["Content-Disposition"] = f'attachment; filename="sailing-manifest-{reference}.pdf"'
            return response

        except Exception as e:
            return Response(
                {"detail": f"Failed to generate PDF manifest via Playwright: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
