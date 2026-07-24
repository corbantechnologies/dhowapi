from django.urls import path
from refund.views import (
    RefundListCreateView,
    RefundDetailView,
    RefundProcessView,
)

app_name = "refund"

urlpatterns = [
    path("", RefundListCreateView.as_view(), name="refund_list_create"),
    path("<str:reference>/", RefundDetailView.as_view(), name="refund_detail"),
    path("<str:reference>/process/", RefundProcessView.as_view(), name="refund_process"),
]
