from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display  = ["hospital", "method", "tier", "amount", "status", "initiated_at"]
    list_filter   = ["method", "status", "tier"]
    search_fields = ["hospital__facility_name", "mpesa_receipt_number"]
    readonly_fields = ["initiated_at", "completed_at"]

    def has_delete_permission(self, request, obj=None):
        return False  # Payment records are immutable