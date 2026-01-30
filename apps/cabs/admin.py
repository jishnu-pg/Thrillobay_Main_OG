from django.contrib import admin
from django.utils.html import format_html
from .models import (
    CabCategory, Cab, CabImage, CabInclusion, 
    CabPolicy, CabPricingOption, CabBooking, CabTransferType
)


@admin.register(CabCategory)
class CabCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(CabTransferType)
class CabTransferTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


class CabImageInline(admin.TabularInline):
    model = CabImage
    extra = 1
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        if obj.image:
            try:
                return format_html('<img src="{}" width="100" height="auto" />', obj.image.url)
            except:
                return "No image"
        return "No image"


class CabInclusionInline(admin.TabularInline):
    model = CabInclusion
    extra = 1


class CabPolicyInline(admin.TabularInline):
    model = CabPolicy
    extra = 1


class CabPricingOptionInline(admin.TabularInline):
    model = CabPricingOption
    extra = 1


@admin.register(Cab)
class CabAdmin(admin.ModelAdmin):
    save_as = True
    list_display = (
        "title", 
        "category", 
        "capacity", 
        "fuel_type", 
        "is_ac", 
        "base_price", 
        "is_active"
    )
    list_filter = ("category", "fuel_type", "is_ac", "is_active", "transfer_types")
    search_fields = ("title", "category__name")
    filter_horizontal = ("transfer_types",)
    inlines = [
        CabImageInline, 
        CabInclusionInline, 
        CabPolicyInline, 
        CabPricingOptionInline
    ]
    
    fieldsets = (
        ("Basic Info", {
            "fields": ("title", "category", "location", "transfer_types", "capacity", "luggage_capacity", "is_active")
        }),
        ("Technical Specs", {
            "fields": ("fuel_type", "is_ac")
        }),
        ("Pricing Configuration", {
            "fields": (
                "base_price", 
                "discount",
                "price_per_km", 
                "included_kms", 
                "extra_km_fare", 
                "driver_allowance", 
                "free_waiting_time_minutes"
            )
        }),
        ("Policies", {
            "fields": ("cancellation_policy",)
        }),
    )


@admin.register(CabBooking)
class CabBookingAdmin(admin.ModelAdmin):
    list_display = (
        "id", 
        "cab", 
        "pickup_location", 
        "drop_location", 
        "pickup_datetime", 
        "status", 
        "total_amount"
    )
    list_filter = ("status", "trip_type", "pickup_datetime")
    search_fields = ("pickup_location", "drop_location", "cab__title")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "pickup_datetime"
