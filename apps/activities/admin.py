from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Activity, ActivityImage, ActivityFeature, ActivityHighlight,
    ActivityItinerary, ActivityPolicy, ActivityInclusion, ActivityType
)

@admin.register(ActivityType)
class ActivityTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

class ActivityImageInline(admin.TabularInline):
    model = ActivityImage
    extra = 1
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        if obj.image:
            try:
                return format_html('<img src="{}" width="100" height="auto" />', obj.image.url)
            except:
                return "No image"
        return "No image"

class ActivityFeatureInline(admin.TabularInline):
    model = ActivityFeature
    extra = 1

class ActivityHighlightInline(admin.TabularInline):
    model = ActivityHighlight
    extra = 1

class ActivityItineraryInline(admin.StackedInline):
    model = ActivityItinerary
    extra = 1

class ActivityInclusionInline(admin.TabularInline):
    model = ActivityInclusion
    extra = 1

class ActivityPolicyInline(admin.StackedInline):
    model = ActivityPolicy
    can_delete = False
    verbose_name_plural = "Activity Policies"

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    save_as = True
    list_display = ("title", "location", "duration_days", "difficulty", "base_price", "is_active", "created_at")
    list_filter = ("is_active", "difficulty", "duration_days", "location", "types")
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "location", "short_description")
    filter_horizontal = ("types",)
    
    inlines = [
        ActivityImageInline,
        ActivityFeatureInline,
        ActivityHighlightInline,
        ActivityItineraryInline,
        ActivityInclusionInline,
        ActivityPolicyInline,
    ]
    
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    fieldsets = (
        ("Basic Information", {
            "fields": ("title", "slug", "location", "types", "short_description", "description", "is_active")
        }),
        ("Experience Details", {
            "fields": (("duration_days", "duration_nights"), "difficulty", ("min_age", "max_age"), "group_size")
        }),
        ("Pricing", {
            "fields": ("base_price", "discount")
        }),
        ("Stats", {
            "fields": ("rating", "review_count"),
            "classes": ("collapse",)
        }),
    )

@admin.register(ActivityItinerary)
class ActivityItineraryAdmin(admin.ModelAdmin):
    list_display = ("activity", "day_number", "title")
    list_filter = ("day_number", "activity__location")
    search_fields = ("title", "description", "activity__title")
    raw_id_fields = ("activity",)
