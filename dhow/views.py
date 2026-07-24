from rest_framework import generics
from accounts.permissions import IsDhowManagerOrReadOnly
from dhow.models import Dhow
from dhow.serializers import DhowSerializer


class DhowListCreateView(generics.ListCreateAPIView):
    queryset = Dhow.objects.all()
    serializer_class = DhowSerializer
    permission_classes = [IsDhowManagerOrReadOnly]
    filterset_fields = ["is_active", "is_available"]
    search_fields = ["name", "reference"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class DhowDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Dhow.objects.all()
    serializer_class = DhowSerializer
    permission_classes = [IsDhowManagerOrReadOnly]
    lookup_field = "reference"
