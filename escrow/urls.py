from django.urls import path
from escrow.views import EscrowRecordListView, EscrowRecordDetailView

app_name = "escrow"

urlpatterns = [
    path("", EscrowRecordListView.as_view(), name="escrow_list"),
    path("<str:reference>/", EscrowRecordDetailView.as_view(), name="escrow_detail"),
]
