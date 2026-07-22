from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from accounts.permissions import IsDhowManagerOrReadOnly, IsDhowManager
from table.models import Table
from table.serializers import TableSerializer


class TableListCreateView(generics.ListCreateAPIView):
    queryset = Table.objects.all()
    serializer_class = TableSerializer
    permission_classes = [IsDhowManagerOrReadOnly]
    filterset_fields = ["schedule", "is_available", "assigned_to"]
    search_fields = ["table_number", "description"]


class TableDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Table.objects.all()
    serializer_class = TableSerializer
    permission_classes = [IsDhowManagerOrReadOnly]


class TableAssignView(APIView):
    permission_classes = [IsDhowManager]

    def patch(self, request, pk):
        table = get_object_or_404(Table, pk=pk)
        booking_id = request.data.get("booking_id")

        if booking_id:
            from booking.models import Booking
            booking = get_object_or_404(Booking, pk=booking_id)
            table.assigned_to = booking
            table.is_available = False
        else:
            table.assigned_to = None
            table.is_available = True

        table.save()
        serializer = TableSerializer(table)
        return Response(serializer.data, status=status.HTTP_200_OK)
