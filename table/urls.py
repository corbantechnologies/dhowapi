from django.urls import path
from table.views import TableListCreateView, TableDetailView, TableAssignView

app_name = "table"

urlpatterns = [
    path("", TableListCreateView.as_view(), name="table_list_create"),
    path("<uuid:pk>/", TableDetailView.as_view(), name="table_detail"),
    path("<uuid:pk>/assign/", TableAssignView.as_view(), name="table_assign"),
]
