from django.contrib import admin
from .models import Booking, BookingItem, BookingTraveller


class BookingItemInline(admin.TabularInline):
    model = BookingItem
    extra = 0
    fields = ('property', 'room_type', 'package', 'activity', 'cab', 'check_in', 'check_out', 'adults', 'children')
    readonly_fields = ('created_at', 'updated_at')


class BookingTravellerInline(admin.TabularInline):
    model = BookingTraveller
    extra = 0
    fields = ('traveller', 'is_primary')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'booking_type', 'status', 'total_amount', 'amount_paid', 'created_at')
    list_filter = ('booking_type', 'status', 'created_at', 'updated_at')
    search_fields = ('id', 'user__username', 'user__email', 'user__phone')
    raw_id_fields = ('user',)
    inlines = [BookingItemInline, BookingTravellerInline]
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Booking Information', {
            'fields': ('user', 'booking_type', 'status')
        }),
        ('Payment Information', {
            'fields': ('total_amount', 'amount_paid')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BookingItem)
class BookingItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'property', 'room_type', 'package', 'activity', 'cab', 'check_in', 'check_out', 'adults', 'children')
    list_filter = ('check_in', 'check_out', 'adults', 'children', 'created_at')
    search_fields = ('booking__id', 'property__name', 'package__title', 'activity__title')
    raw_id_fields = ('booking', 'property', 'room_type', 'package', 'activity', 'cab')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)


@admin.register(BookingTraveller)
class BookingTravellerAdmin(admin.ModelAdmin):
    list_display = ('booking', 'traveller', 'is_primary')
    list_filter = ('is_primary',)
    search_fields = ('booking__id', 'traveller__first_name', 'traveller__last_name', 'traveller__email')
    raw_id_fields = ('booking', 'traveller')
    ordering = ('-booking__created_at',)
