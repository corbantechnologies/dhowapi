from rest_framework import generics
from accounts.permissions import IsDhowManager
from escrow.models import EscrowRecord
from escrow.serializers import EscrowRecordSerializer


class EscrowRecordListView(generics.ListAPIView):
    queryset = EscrowRecord.objects.all()
    serializer_class = EscrowRecordSerializer
    permission_classes = [IsDhowManager]
    filterset_fields = ["schedule", "status", "resolution_method"]
    search_fields = ["reference", "payment__reference", "payment__booking__reference"]


class EscrowRecordDetailView(generics.RetrieveAPIView):
    queryset = EscrowRecord.objects.all()
    serializer_class = EscrowRecordSerializer
    permission_classes = [IsDhowManager]
    lookup_field = "reference"
