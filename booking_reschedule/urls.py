from django.urls import path
from booking_reschedule.views import (
    BookingRescheduleListCreateView,
    BookingRescheduleDetailView,
    BookingRescheduleConfirmView,
)

app_name = "booking_reschedule"

urlpatterns = [
    path("", BookingRescheduleListCreateView.as_view(), name="booking_reschedule_list_create"),
    path("<str:reference>/", BookingRescheduleDetailView.as_view(), name="booking_reschedule_detail"),
    path("<str:reference>/confirm/", BookingRescheduleConfirmView.as_view(), name="booking_reschedule_confirm"),
]
