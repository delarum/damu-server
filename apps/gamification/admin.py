from django.contrib import admin
from .models import Badge, DonorBadge, DonationRecord, CreditLedger


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ["icon", "name", "title", "required_donations"]
    ordering     = ["required_donations"]


@admin.register(DonorBadge)
class DonorBadgeAdmin(admin.ModelAdmin):
    list_display  = ["donor", "badge", "earned_at"]
    search_fields = ["donor__user__full_name"]


@admin.register(DonationRecord)
class DonationRecordAdmin(admin.ModelAdmin):
    list_display  = ["donor", "hospital", "donation_type", "donation_date", "credits_awarded"]
    list_filter   = ["donation_type"]
    search_fields = ["donor__user__full_name", "hospital__facility_name"]


@admin.register(CreditLedger)
class CreditLedgerAdmin(admin.ModelAdmin):
    list_display  = ["donor", "transaction_type", "amount", "balance_after", "reason", "created_at"]
    list_filter   = ["transaction_type"]
    search_fields = ["donor__user__full_name"]

    def has_change_permission(self, request, obj=None):
        return False  # Ledger is immutable

    def has_delete_permission(self, request, obj=None):
        return False  # Ledger is immutable