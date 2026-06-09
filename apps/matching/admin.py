from django.contrib import admin
from .models import ContactRequest


@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    list_display  = ["hospital", "donor", "status", "requested_at", "expires_at"]
    list_filter   = ["status"]
    search_fields = ["hospital__facility_name", "donor__user__full_name"]
    readonly_fields = ["requested_at", "responded_at"]