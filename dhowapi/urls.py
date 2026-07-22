from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("accounts.urls")),
    path("api/v1/dhows/", include("dhow.urls")),
    path("api/v1/packages/", include("package.urls")),
    path("api/v1/addons/", include("addon.urls")),
    path("api/v1/schedule-templates/", include("schedule_template.urls")),
    path("api/v1/schedules/", include("schedule.urls")),
    path("api/v1/tables/", include("table.urls")),
    path("api/v1/bookings/", include("booking.urls")),
    path("api/v1/booking-guests/", include("booking_guest.urls")),
    path("api/v1/booking-addons/", include("booking_addon.urls")),
    path("api/v1/booking-reschedules/", include("booking_reschedule.urls")),
    path("api/v1/booking-status-logs/", include("booking_status_log.urls")),
    path("api/v1/payments/", include("payment.urls")),
    path("api/v1/escrow/", include("escrow.urls")),
    path("api/v1/refunds/", include("refund.urls")),
    path("api/v1/refund-logs/", include("refund_log.urls")),
]
