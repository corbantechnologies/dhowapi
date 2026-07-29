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
            # Token signature expires after 24 hours (86400 seconds)
            payload = signing.loads(token, salt="manifest-share", max_age=86400)
            schedule_ref = payload.get("schedule_ref")
            if not schedule_ref:
                return False
            
            # Save the validated reference on the request for views to use
            request.manifest_schedule_ref = schedule_ref
            return True
        except signing.SignatureExpired:
            return False
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
