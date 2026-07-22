from django.urls import path
from schedule_template.views import (
    ScheduleTemplateListCreateView,
    ScheduleTemplateDetailView,
)

app_name = "schedule_template"

urlpatterns = [
    path("", ScheduleTemplateListCreateView.as_view(), name="schedule_template_list_create"),
    path("<str:reference>/", ScheduleTemplateDetailView.as_view(), name="schedule_template_detail"),
]
