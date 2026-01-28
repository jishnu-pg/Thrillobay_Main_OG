from django.contrib import admin
from .models import Coupon, CouponUsage


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_amount', 'valid_from', 'valid_to', 'created_at')
    list_filter = ('valid_from', 'valid_to', 'created_at', 'updated_at')
    search_fields = ('code',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ('coupon', 'booking', 'user', 'created_at')
    list_filter = ('created_at', 'updated_at', 'coupon__code')
    search_fields = ('coupon__code', 'booking__id', 'user__username', 'user__email')
    raw_id_fields = ('coupon', 'booking', 'user')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
