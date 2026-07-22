from rest_framework import generics
from accounts.permissions import IsDhowManagerOrReadOnly
from package.models import Package
from package.serializers import PackageSerializer


class PackageListCreateView(generics.ListCreateAPIView):
    queryset = Package.objects.all()
    serializer_class = PackageSerializer
    permission_classes = [IsDhowManagerOrReadOnly]
    filterset_fields = ["meal_type", "is_active"]
    search_fields = ["name", "reference"]


class PackageDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Package.objects.all()
    serializer_class = PackageSerializer
    permission_classes = [IsDhowManagerOrReadOnly]
    lookup_field = "reference"
