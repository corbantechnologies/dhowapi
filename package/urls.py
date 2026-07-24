from django.urls import path
from package.views import PackageListCreateView, PackageDetailView

app_name = "package"

urlpatterns = [
    path("", PackageListCreateView.as_view(), name="package_list_create"),
    path("<str:reference>/", PackageDetailView.as_view(), name="package_detail"),
]
