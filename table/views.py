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


class TableBulkCreateView(APIView):
    permission_classes = [IsDhowManager]

    def post(self, request, *args, **kwargs):
        schedule_id = request.data.get("schedule")
        tables_list = request.data.get("tables", [])

        if not schedule_id:
            return Response({"error": "Schedule is required."}, status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(tables_list, list) or len(tables_list) == 0:
            return Response({"error": "A list of tables is required."}, status=status.HTTP_400_BAD_REQUEST)

        from schedule.models import Schedule
        from django.db.models import Sum
        schedule = get_object_or_404(Schedule, pk=schedule_id)
        dhow = schedule.dhow
        max_capacity = dhow.total_capacity

        # Calculate current capacity of existing tables
        existing_capacity = Table.objects.filter(schedule=schedule).aggregate(total=Sum('capacity'))['total'] or 0

        # Calculate new capacity
        try:
            new_total_capacity = sum(int(t.get("capacity", 4)) for t in tables_list)
        except (ValueError, TypeError):
            return Response({"error": "Capacity must be an integer for all tables."}, status=status.HTTP_400_BAD_REQUEST)

        if existing_capacity + new_total_capacity > max_capacity:
            return Response(
                {
                    "non_field_errors": [
                        f"Cannot create tables. Total table capacity ({existing_capacity + new_total_capacity}) would exceed vessel capacity ({max_capacity}). Current table capacity: {existing_capacity}."
                    ]
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate duplicate table numbers
        seen_table_numbers = set()
        for idx, t in enumerate(tables_list):
            num = t.get("table_number")
            if not num:
                return Response({"error": f"Table number is required for item at index {idx}."}, status=status.HTTP_400_BAD_REQUEST)
            if num in seen_table_numbers:
                return Response({"error": f"Duplicate table number '{num}' in request list."}, status=status.HTTP_400_BAD_REQUEST)
            seen_table_numbers.add(num)
            if Table.objects.filter(schedule=schedule, table_number=num).exists():
                return Response({"error": f"Table number '{num}' already exists for this sailing voyage schedule."}, status=status.HTTP_400_BAD_REQUEST)

        # Create tables
        created_tables = []
        for t in tables_list:
            table = Table.objects.create(
                schedule=schedule,
                table_number=t.get("table_number"),
                capacity=int(t.get("capacity", 4)),
                description=t.get("description", ""),
                is_available=True
            )
            created_tables.append(table)

        serializer = TableSerializer(created_tables, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
