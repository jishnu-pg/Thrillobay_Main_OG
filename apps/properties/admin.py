from django.contrib import admin
from django.utils.html import format_html
from .models import Property, RoomType, PropertyImage, RoomTypeImage, Discount, Amenity


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ("name", "discount_type", "value", "is_active")
    list_filter = ("discount_type", "is_active")
    search_fields = ("name",)


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ("name", "icon_preview")
    search_fields = ("name",)

    def icon_preview(self, obj):
        if obj.icon:
            return format_html('<img src="{}" width="30" height="30" />', obj.icon.url)
        return "No Icon"


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        if obj.image:
            try:
                return format_html('<img src="{}" width="100" height="auto" />', obj.image.url)
            except:
                return "No image"
        return "No image"


class RoomTypeImageInline(admin.TabularInline):
    model = RoomTypeImage
    extra = 1
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        if obj.image:
            try:
                return format_html('<img src="{}" width="100" height="auto" />', obj.image.url)
            except:
                return "No image"
        return "No image"


class RoomTypeInline(admin.TabularInline):
    model = RoomType
    extra = 0
    fields = ("name", "max_guests", "base_price", "total_units", "has_breakfast")


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "city",
        "property_type",
        "star_rating",
        "discount",
        "gst_percent",
        "is_active",
    )
    list_filter = (
        "property_type",
        "star_rating",
        "is_active",
        "discount",
        "city",
        "state",
    )
    search_fields = ("name", "city", "state", "description")
    inlines = [RoomTypeInline, PropertyImageInline]
    filter_horizontal = ("amenities",)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    fieldsets = (
        ("Basic Information", {
            "fields": ("name", "property_type", "description", "is_active")
        }),
        ("Location", {
            "fields": ("city", "area", "state")
        }),
        ("Ratings & Reviews", {
            "fields": ("star_rating", "review_rating", "review_count")
        }),
        ("Amenities & Discounts", {
            "fields": ("amenities", "discount")
        }),
        ("House Rules & Policies", {
            "fields": ("check_in_time", "check_out_time", "rules")
        }),
        ("Financials", {
            "fields": ("gst_percent",)
        }),
        ("Entire Place Booking Configuration", {
            "fields": ("allow_entire_place_booking", "entire_place_price", "entire_place_max_guests"),
            "classes": ("collapse",),
            "description": "Enable this to allow users to book the entire property at a special price."
        }),
    )


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "property",
        "max_guests",
        "base_price",
        "total_units",
        "has_breakfast",
    )
    list_filter = ("has_breakfast", "max_guests", "property__property_type")
    search_fields = ("name", "property__name")
    raw_id_fields = ("property",)
    inlines = [RoomTypeImageInline]
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    fieldsets = (
        ("Basic Information", {
            "fields": ("property", "name", "max_guests", "bedroom_count", "is_entire_place")
        }),
        ("Pricing & Policies", {
            "fields": ("base_price", "has_breakfast", "refund_policy", "booking_policy")
        }),
        ("Inventory", {
            "fields": ("total_units",)
        }),
    )
