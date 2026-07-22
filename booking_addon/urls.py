from django.urls import path
from booking_addon.views import BookingAddOnListCreateView, BookingAddOnDetailView

app_name = "booking_addon"

urlpatterns = [
    path("", BookingAddOnListCreateView.as_view(), name="booking_addon_list_create"),
    path("<uuid:pk>/", BookingAddOnDetailView.as_view(), name="booking_addon_detail"),
]
