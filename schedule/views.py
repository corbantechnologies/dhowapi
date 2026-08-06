import resend
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.conf import settings
from datetime import datetime

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


from rest_framework.permissions import IsAuthenticated
from schedule.permissions import HasManifestAccessToken


class SchedulePublicManifestView(APIView):
    permission_classes = [IsAuthenticated | HasManifestAccessToken]

    def get(self, request, reference):
        schedule = get_object_or_404(Schedule, reference=reference)

        # Secure access check: validate manifest token matches this schedule
        if not request.user.is_authenticated:
            token = request.headers.get("X-Manifest-Token") or request.query_params.get("token")
            if not token or schedule.manifest_token != token:
                return Response(
                    {"detail": "You do not have permission to view this manifest."},
                    status=status.HTTP_403_FORBIDDEN
                )

        # Get all confirmed or completed bookings for this schedule
        bookings = schedule.bookings.filter(
            status__in=["confirmed", "completed", "pending", "no_show"]
        ).order_by("created_at")

        # Format manifest records
        manifest_data = []
        for b in bookings:
            # Get table numbers
            tables = b.assigned_tables.all()
            table_numbers = b.table_allocation or (", ".join([t.table_number for t in tables]) if tables.exists() else "")

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

            addons_data = []
            for ba in b.booking_addons.all():
                addons_data.append({
                    "addon_name": ba.addon.name,
                    "quantity": ba.quantity,
                    "total_price": float(ba.total_price),
                })

            manifest_data.append({
                "id": b.id,
                "reference": b.reference,
                "booked_by_name": booked_by_name,
                "party_size": b.party_size,
                "adult_count": b.adult_count,
                "child_count": b.child_count,
                "table_number": table_numbers,
                "table_allocation": b.table_allocation,
                "special_requests": b.special_requests or "",
                "status": b.status,
                "booking_guests": guests_data,
                "booking_addons": addons_data,
                "total_amount": float(b.total_amount),
                "total_paid": float(b.total_paid),
                "outstanding_balance": float(b.outstanding_balance),
                "discount_amount": float(b.discount_amount),
                "payments": [
                    {
                        "amount": float(p.amount),
                        "payment_method": p.get_payment_method_display(),
                        "ref": p.receipt_number or p.transaction_ref or p.reference
                    }
                    for p in b.payments.filter(status="completed")
                ]
            })

        data = {
            "schedule": {
                "id": str(schedule.id),
                "reference": schedule.reference,
                "dhow_name": schedule.dhow.name,
                "date": str(schedule.date),
                "meal_type_display": schedule.get_meal_type_display(),
                "departure_time": str(schedule.departure_time),
                "return_time": str(schedule.return_time),
                "price_per_person": float(schedule.price_per_person),
                "price_per_child": float(schedule.price_per_child or 0.0),
                "status": schedule.status,
            },
            "manifest": manifest_data
        }
        return Response(data, status=status.HTTP_200_OK)


class SchedulePDFDownloadView(APIView):
    permission_classes = [IsAuthenticated | HasManifestAccessToken]  # Public sharing token authorized

    def get(self, request, reference):
        from django.http import HttpResponse
        from django.template.loader import render_to_string
        from playwright.sync_api import sync_playwright
        import traceback
        import os

        try:
            schedule = get_object_or_404(Schedule, reference=reference)

            # Secure access check: validate manifest token matches this schedule
            if not request.user.is_authenticated:
                token = request.headers.get("X-Manifest-Token") or request.query_params.get("token")
                if not token or schedule.manifest_token != token:
                    return HttpResponse("Forbidden", status=403)

            # Get all confirmed or completed/pending bookings for this schedule
            bookings = schedule.bookings.filter(
                status__in=["confirmed", "completed", "pending", "no_show"]
            ).order_by("created_at")

            manifest_list = []
            for b in bookings:
                # Table seating allocation
                tables = b.assigned_tables.all()
                table_number = b.table_allocation or (", ".join([t.table_number for t in tables]) if tables.exists() else "")

                # Resolve primary guest details
                primary_guest = b.booking_guests.filter(is_primary=True).first()
                if primary_guest:
                    booked_by_name = f"{primary_guest.first_name} {primary_guest.last_name}"
                    email = primary_guest.email or ""
                    phone = primary_guest.phone or ""
                elif b.booked_by:
                    booked_by_name = b.booked_by.get_full_name() or b.booked_by.username
                    email = b.booked_by.email
                    phone = getattr(b.booked_by, "phone_number", "")
                else:
                    booked_by_name = "Walk-In Guest"
                    email = ""
                    phone = ""

                addons_list = []
                for ba in b.booking_addons.all():
                    addons_list.append({
                        "name": ba.addon.name,
                        "quantity": ba.quantity,
                    })

                manifest_list.append({
                    "reference": b.reference,
                    "booked_by_name": booked_by_name,
                    "email": email,
                    "phone": phone,
                    "party_size": b.party_size,
                    "adult_count": b.adult_count,
                    "child_count": b.child_count,
                    "table_number": table_number,
                    "table_allocation": b.table_allocation,
                    "special_requests": b.special_requests or "",
                    "status": b.status,
                    "status_display": b.get_status_display(),
                    "addons_list": addons_list,
                    "total_amount": float(b.total_amount),
                    "total_paid": float(b.total_paid),
                    "outstanding_balance": float(b.outstanding_balance),
                    "discount_amount": float(b.discount_amount),
                    "payments": [
                        {
                            "amount": float(p.amount),
                            "payment_method": p.get_payment_method_display(),
                            "ref": p.receipt_number or p.transaction_ref or p.reference
                        }
                        for p in b.payments.filter(status="completed")
                    ]
                })

            # Render HTML template natively on the backend
            context = {
                "schedule": schedule,
                "bookings": bookings,
                "manifest_list": manifest_list,
                "total_pax": sum(b.party_size for b in bookings),
            }
            html_content = render_to_string("schedule/pdf_manifest.html", context)

            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-setuid-sandbox"]
                )
                page = browser.new_page()

                # Directly load HTML content on the browser page — no network calls
                page.set_content(html_content, wait_until="networkidle")

                pdf_bytes = page.pdf(
                    format="A4",
                    landscape=True,
                    prefer_css_page_size=True,
                    print_background=True,
                    margin={"top": "0.4in", "right": "0.4in", "bottom": "0.4in", "left": "0.4in"}
                )
                # browser is closed automatically when the `with` block exits

            response = HttpResponse(pdf_bytes, content_type="application/pdf")
            response["Content-Disposition"] = f'attachment; filename="sailing-manifest-{reference}.pdf"'
            return response

        except Exception as e:
            traceback.print_exc()
            return Response(
                {"detail": f"Failed to generate PDF manifest: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ScheduleShareView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, reference):
        

        schedule = get_object_or_404(Schedule, reference=reference)
        recipient_email = request.data.get("email")

        # Ensure a permanent token exists (auto-generated on first schedule save)
        if not schedule.manifest_token:
            schedule.manifest_token = __import__("uuid").uuid4().hex
            schedule.save(update_fields=["manifest_token"])

        # Use the configured FRONTEND_URL from settings to build the public manifest link
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
        share_url = f"{frontend_url}/manifest/{reference}?token={schedule.manifest_token}"

        # Send email to supervisor if email is provided
        if recipient_email:
            dep_time = schedule.departure_time.strftime("%H:%M") if hasattr(schedule.departure_time, "strftime") else str(schedule.departure_time)[:5]
            ret_time = schedule.return_time.strftime("%H:%M") if hasattr(schedule.return_time, "strftime") else str(schedule.return_time)[:5]

            # Render branded HTML email from template
            email_html = render_to_string("schedule/manifest_share_email.html", {
                "dhow_name": schedule.dhow.name,
                "date": str(schedule.date),
                "meal_type": schedule.get_meal_type_display(),
                "departure_time": dep_time,
                "return_time": ret_time,
                "share_url": share_url,
                "current_year": datetime.now().year,
            })

            params = {
                "from": "Dhow Operations <dhow-onboarding@tamarind.co.ke>",
                "to": [recipient_email],
                "subject": f"Crew Manifest Access: {schedule.dhow.name} — {schedule.date}",
                "html": email_html,
            }

            try:
                resend.api_key = settings.RESEND_API_KEY
                resend.Emails.send(params)
                return Response(
                    {"detail": f"Manifest link successfully emailed to {recipient_email}.", "share_url": share_url},
                    status=status.HTTP_200_OK
                )
            except Exception as e:
                return Response(
                    {"detail": f"Email dispatch failed: {str(e)}", "share_url": share_url},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response({"share_url": share_url}, status=status.HTTP_200_OK)

