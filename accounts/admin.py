from django.contrib import admin
from django.contrib.auth import get_user_model

User = get_user_model()


class UserAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "username",
        "first_name",
        "last_name",
        "phone_number",
        "country",
        "city",
        "address",
        "is_staff",
        "is_superuser",
        "is_dhow_manager",
        "is_guest",
        "is_agent",
        "is_active",
        "created_at",
        "updated_at",
    )
    list_filter = (
        "is_staff",
        "is_superuser",
        "is_dhow_manager",
        "is_guest",
        "is_agent",
        "is_active",
    )
    search_fields = (
        "email",
        "username",
        "first_name",
        "last_name",
        "phone_number",
        "usercode",
    )
    ordering = ("-created_at",)


admin.site.register(User, UserAdmin)
