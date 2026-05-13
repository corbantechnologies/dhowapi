from django.urls import path

from accounts.views import (
    TokenView,
    UserListView,
    UserDetailView,
    DhowManagerCreateView,
    GuestUserCreateView,
    AgentUserCreateView,
    ForgotPasswordView,
    ResetPasswordView,
)

app_name = "accounts"

urlpatterns = [
    path("token/", TokenView.as_view(), name="token"),
    path("", UserListView.as_view(), name="user_list"),
    path("<str:usercode>/", UserDetailView.as_view(), name="user_detail"),
    path(
        "dhow-managers/signup/",
        DhowManagerCreateView.as_view(),
        name="dhow_manager_create",
    ),
    path("guests/signup/", GuestUserCreateView.as_view(), name="guest_user_create"),
    path("agents/signup/", AgentUserCreateView.as_view(), name="agent_user_create"),
    path("password/forgot/", ForgotPasswordView.as_view(), name="forgot_password"),
    path("password/reset/", ResetPasswordView.as_view(), name="reset_password"),
]
