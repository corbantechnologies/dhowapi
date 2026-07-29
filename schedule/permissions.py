from rest_framework.permissions import BasePermission
from django.core import signing
from schedule.models import Schedule
from booking_guest.models import BookingGuest

class HasManifestAccessToken(BasePermission):
    def has_permission(self, request, view):
        # Extract token from headers or query parameters
        token = request.headers.get("X-Manifest-Token") or request.query_params.get("token")
        if not token:
            return False

        try:
            # Load without max_age, signature verification still holds
            payload = signing.loads(token, salt="manifest-share")
            schedule_ref = payload.get("schedule_ref")
            if not schedule_ref:
                return False
            
            # Fetch schedule to check date
            schedule = Schedule.objects.filter(reference=schedule_ref).first()
            if not schedule:
                return False
            
            # Check if sailing date has passed
            from datetime import date
            if schedule.date < date.today():
                return False
            
            # Save the validated reference on the request for views to use
            request.manifest_schedule_ref = schedule_ref
            return True
        except signing.BadSignature:
            return False

    def has_object_permission(self, request, view, obj):
        schedule_ref = getattr(request, "manifest_schedule_ref", None)
        if not schedule_ref:
            return False

        if isinstance(obj, Schedule):
            return obj.reference == schedule_ref

        if isinstance(obj, BookingGuest):
            return obj.booking.schedule.reference == schedule_ref

        return False
