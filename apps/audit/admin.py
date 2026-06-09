from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display  = ["timestamp", "actor", "actor_role", "action", "endpoint", "ip_address"]
    list_filter   = ["action", "actor_role"]
    search_fields = ["actor__full_name", "actor__phone", "endpoint"]
    readonly_fields = [f.name for f in AuditLog._meta.get_fields() if hasattr(f, 'name')]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False