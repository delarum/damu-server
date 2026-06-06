from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, OTPVerification


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ["phone", "full_name", "role", "is_verified", "is_active", "created_at"]
    list_filter   = ["role", "is_verified", "is_active"]
    search_fields = ["phone", "full_name", "email", "national_id"]
    ordering      = ["-created_at"]

    fieldsets = (
        (None,            {"fields": ("phone", "password")}),
        ("Personal info", {"fields": ("full_name", "email", "national_id", "date_of_birth")}),
        ("Role & Status", {"fields": ("role", "is_verified", "is_active", "is_staff")}),
        ("Permissions",   {"fields": ("groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields":  ("phone", "full_name", "role", "password1", "password2"),
        }),
    )


@admin.register(OTPVerification)
class OTPAdmin(admin.ModelAdmin):
    list_display  = ["user", "purpose", "is_used", "created_at", "expires_at"]
    list_filter   = ["purpose", "is_used"]
    search_fields = ["user__phone"]