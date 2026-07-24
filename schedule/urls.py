from django.urls import path
from schedule.views import (
    ScheduleListCreateView,
    ScheduleDetailView,
    ScheduleOpenView,
    ScheduleCloseView,
    ScheduleConfirmView,
    ScheduleCancelView,
)

app_name = "schedule"

urlpatterns = [
    path("", ScheduleListCreateView.as_view(), name="schedule_list_create"),
    path("<str:reference>/", ScheduleDetailView.as_view(), name="schedule_detail"),
    path("<str:reference>/open/", ScheduleOpenView.as_view(), name="schedule_open"),
    path("<str:reference>/close/", ScheduleCloseView.as_view(), name="schedule_close"),
    path("<str:reference>/confirm/", ScheduleConfirmView.as_view(), name="schedule_confirm"),
    path("<str:reference>/cancel/", ScheduleCancelView.as_view(), name="schedule_cancel"),
]
