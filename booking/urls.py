from django.urls import path
from booking.views import (
    BookingListCreateView,
    BookingDetailView,
    BookingCancelView,
    BookingNoShowView,
    BookingAssignTableView,
    BookingBulkCreateView,
    BookingPublicTicketView,
)

app_name = "booking"

urlpatterns = [
    path("", BookingListCreateView.as_view(), name="booking_list_create"),
    path("bulk/", BookingBulkCreateView.as_view(), name="booking_bulk_create"),
    path("<str:reference>/", BookingDetailView.as_view(), name="booking_detail"),
    path("<str:reference>/ticket/", BookingPublicTicketView.as_view(), name="booking_public_ticket"),
    path("<str:reference>/cancel/", BookingCancelView.as_view(), name="booking_cancel"),
    path("<str:reference>/no-show/", BookingNoShowView.as_view(), name="booking_no_show"),
    path("<str:reference>/assign-table/", BookingAssignTableView.as_view(), name="booking_assign_table"),
]

