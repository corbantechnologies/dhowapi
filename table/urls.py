from django.urls import path
from table.views import TableListCreateView, TableDetailView, TableAssignView, TableBulkCreateView

app_name = "table"

urlpatterns = [
    path("", TableListCreateView.as_view(), name="table_list_create"),
    path("bulk/", TableBulkCreateView.as_view(), name="table_bulk_create"),
    path("<uuid:pk>/", TableDetailView.as_view(), name="table_detail"),
    path("<uuid:pk>/assign/", TableAssignView.as_view(), name="table_assign"),
]
