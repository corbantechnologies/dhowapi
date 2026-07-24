from django.urls import path
from payment.views import (
    PaymentListCreateView,
    PaymentDetailView,
    MpesaSTKInitiateView,
    MpesaCallbackView,
)

app_name = "payment"

urlpatterns = [
    path("", PaymentListCreateView.as_view(), name="payment_list_create"),
    path("mpesa/initiate/", MpesaSTKInitiateView.as_view(), name="mpesa_initiate"),
    path("mpesa/callback/", MpesaCallbackView.as_view(), name="mpesa_callback"),
    path("<str:reference>/", PaymentDetailView.as_view(), name="payment_detail"),
]
