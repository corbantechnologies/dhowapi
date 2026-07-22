from django.urls import path
from refund_log.views import (
    RefundStatusLogListCreateView,
    RefundStatusLogDetailView,
)

app_name = "refund_log"

urlpatterns = [
    path("", RefundStatusLogListCreateView.as_view(), name="refund_log_list_create"),
    path("<uuid:pk>/", RefundStatusLogDetailView.as_view(), name="refund_log_detail"),
]
