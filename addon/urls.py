from django.urls import path
from addon.views import AddOnListCreateView, AddOnDetailView

app_name = "addon"

urlpatterns = [
    path("", AddOnListCreateView.as_view(), name="addon_list_create"),
    path("<str:reference>/", AddOnDetailView.as_view(), name="addon_detail"),
]
