from django.urls import path
from booking_status_log.views import (
    BookingStatusLogListCreateView,
    BookingStatusLogDetailView,
)

app_name = "booking_status_log"

urlpatterns = [
    path("", BookingStatusLogListCreateView.as_view(), name="booking_status_log_list_create"),
    path("<uuid:pk>/", BookingStatusLogDetailView.as_view(), name="booking_status_log_detail"),
]
