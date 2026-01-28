from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'phone', 'first_name', 'last_name', 'is_phone_verified', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'is_superuser', 'is_phone_verified', 'date_joined', 'otp_created_at')
    search_fields = ('username', 'email', 'phone', 'first_name', 'last_name', 'otp_token')
    ordering = ('-date_joined',)
    readonly_fields = ('otp_token', 'otp_created_at', 'date_joined', 'last_login')
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('phone',)}),
        ('OTP Verification', {
            'fields': ('otp_token', 'otp_created_at', 'is_phone_verified'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('phone',)}),
    )
