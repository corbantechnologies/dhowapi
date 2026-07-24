from django.urls import path
from dhow.views import DhowListCreateView, DhowDetailView

app_name = "dhow"

urlpatterns = [
    path("", DhowListCreateView.as_view(), name="dhow_list_create"),
    path("<str:reference>/", DhowDetailView.as_view(), name="dhow_detail"),
]
