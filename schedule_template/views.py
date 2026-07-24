from rest_framework import generics
from accounts.permissions import IsDhowManagerOrReadOnly
from schedule_template.models import ScheduleTemplate
from schedule_template.serializers import ScheduleTemplateSerializer


class ScheduleTemplateListCreateView(generics.ListCreateAPIView):
    queryset = ScheduleTemplate.objects.all()
    serializer_class = ScheduleTemplateSerializer
    permission_classes = [IsDhowManagerOrReadOnly]
    filterset_fields = ["dhow", "meal_type", "is_active"]
    search_fields = ["reference", "dhow__name"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ScheduleTemplateDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ScheduleTemplate.objects.all()
    serializer_class = ScheduleTemplateSerializer
    permission_classes = [IsDhowManagerOrReadOnly]
    lookup_field = "reference"
