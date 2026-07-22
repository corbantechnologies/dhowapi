from django.urls import path
from booking_guest.views import BookingGuestListCreateView, BookingGuestDetailView

app_name = "booking_guest"

urlpatterns = [
    path("", BookingGuestListCreateView.as_view(), name="booking_guest_list_create"),
    path("<uuid:pk>/", BookingGuestDetailView.as_view(), name="booking_guest_detail"),
]
