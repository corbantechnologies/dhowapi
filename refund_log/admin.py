from django.contrib import admin
from refund_log.models import RefundStatusLog


@admin.register(RefundStatusLog)
class RefundStatusLogAdmin(admin.ModelAdmin):
    list_display = ("refund", "old_status", "new_status", "changed_by", "created_at")
    list_filter = ("old_status", "new_status")
    search_fields = ("refund__reference", "changed_by__email")
