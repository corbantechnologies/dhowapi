from rest_framework.permissions import BasePermission
from schedule.models import Schedule
from booking_guest.models import BookingGuest


class HasManifestAccessToken(BasePermission):
    """
    Validates the permanent manifest_token stored on the Schedule model.
    The token is a UUID hex string that never changes or expires.
    Access is revoked only after the sailing date has passed.
    """

    def has_permission(self, request, view):
        # Extract token from headers or query parameters
        token = request.headers.get("X-Manifest-Token") or request.query_params.get("token")
        if not token:
            return False

        # Find a schedule with a matching manifest_token
        schedule = Schedule.objects.filter(manifest_token=token).first()
        if not schedule:
            return False

        # Revoke access if the sailing date has passed
        from datetime import date
        if schedule.date < date.today():
            return False

        # Attach the validated schedule reference to the request for views to use
        request.manifest_schedule_ref = schedule.reference
        return True

    def has_object_permission(self, request, view, obj):
        schedule_ref = getattr(request, "manifest_schedule_ref", None)
        if not schedule_ref:
            return False

        if isinstance(obj, Schedule):
            return obj.reference == schedule_ref

        if isinstance(obj, BookingGuest):
            return obj.booking.schedule.reference == schedule_ref

        # Support Booking objects — allow supervisors to cancel/no-show bookings
        from booking.models import Booking
        if isinstance(obj, Booking):
            return obj.schedule.reference == schedule_ref

        return False
