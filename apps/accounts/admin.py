from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, OTPVerification


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ["email", "full_name", "role", "is_verified", "is_active", "is_staff", "created_at"]
    list_filter   = ["role", "is_verified", "is_active", "is_staff"]
    search_fields = ["email", "full_name", "phone", "national_id"]
    ordering      = ["-created_at"]

    fieldsets = (
        (None,            {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("full_name", "phone", "national_id", "date_of_birth")}),
        ("Role & Status", {"fields": ("role", "is_verified", "is_active", "is_staff")}),
        ("Permissions",   {"fields": ("groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields":  ("email", "full_name", "role", "password1", "password2"),
        }),
    )


@admin.register(OTPVerification)
class OTPAdmin(admin.ModelAdmin):
    list_display  = ["user", "purpose", "is_used", "created_at", "expires_at"]
    list_filter   = ["purpose", "is_used"]
    search_fields = ["user__email", "user__full_name"]
    readonly_fields = ["code", "user", "purpose", "created_at", "expires_at"]
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
