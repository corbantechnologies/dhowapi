from rest_framework import generics
from accounts.permissions import IsDhowManagerOrReadOnly
from addon.models import AddOn
from addon.serializers import AddOnSerializer


class AddOnListCreateView(generics.ListCreateAPIView):
    queryset = AddOn.objects.all()
    serializer_class = AddOnSerializer
    permission_classes = [IsDhowManagerOrReadOnly]
    filterset_fields = ["is_available"]
    search_fields = ["name", "reference"]


class AddOnDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = AddOn.objects.all()
    serializer_class = AddOnSerializer
    permission_classes = [IsDhowManagerOrReadOnly]
    lookup_field = "reference"
