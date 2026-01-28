from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'payment_mode', 'amount', 'status', 'transaction_id', 'created_at')
    list_filter = ('payment_mode', 'status', 'created_at', 'updated_at')
    search_fields = ('id', 'transaction_id', 'booking__id', 'booking__user__username', 'booking__user__email')
    raw_id_fields = ('booking',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
