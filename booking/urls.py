from django.urls import path
from booking.views import (
    BookingListCreateView,
    BookingDetailView,
    BookingCancelView,
    BookingAssignTableView,
)

app_name = "booking"

urlpatterns = [
    path("", BookingListCreateView.as_view(), name="booking_list_create"),
    path("<str:reference>/", BookingDetailView.as_view(), name="booking_detail"),
    path("<str:reference>/cancel/", BookingCancelView.as_view(), name="booking_cancel"),
    path("<str:reference>/assign-table/", BookingAssignTableView.as_view(), name="booking_assign_table"),
]
