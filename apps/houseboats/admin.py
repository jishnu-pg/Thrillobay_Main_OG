from django.contrib import admin
from django.utils.html import format_html
from .models import (
    HouseBoat, HouseBoatImage, HouseBoatSpecification,
    HouseBoatTiming, HouseBoatMealPlan, HouseBoatRoute,
    HouseBoatPolicy, HouseBoatInclusion
)

class HouseBoatImageInline(admin.TabularInline):
    model = HouseBoatImage
    extra = 1
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        if obj.image:
            try:
                return format_html('<img src="{}" width="100" height="auto" />', obj.image.url)
            except:
                return "No image"
        return "No image"

class HouseBoatSpecificationInline(admin.StackedInline):
    model = HouseBoatSpecification
    can_delete = False
    verbose_name_plural = "Houseboat Specifications"

class HouseBoatTimingInline(admin.StackedInline):
    model = HouseBoatTiming
    can_delete = False
    verbose_name_plural = "Houseboat Timings"

class HouseBoatMealPlanInline(admin.StackedInline):
    model = HouseBoatMealPlan
    can_delete = False
    verbose_name_plural = "Meal Plan & Food Rules"

class HouseBoatPolicyInline(admin.StackedInline):
    model = HouseBoatPolicy
    can_delete = False
    verbose_name_plural = "Policies & Rules"

class HouseBoatRouteInline(admin.TabularInline):
    model = HouseBoatRoute
    extra = 1

class HouseBoatInclusionInline(admin.TabularInline):
    model = HouseBoatInclusion
    extra = 1

@admin.register(HouseBoat)
class HouseBoatAdmin(admin.ModelAdmin):
    save_as = True
    list_display = ("name", "location", "base_price_per_night", "rating", "is_active", "created_at")
    list_filter = ("is_active", "location", "rating")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "location", "description")
    
    inlines = [
        HouseBoatImageInline,
        HouseBoatSpecificationInline,
        HouseBoatTimingInline,
        HouseBoatMealPlanInline,
        HouseBoatRouteInline,
        HouseBoatInclusionInline,
        HouseBoatPolicyInline,
    ]
    
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    # Organising core houseboat fields
    fieldsets = (
        ("Basic Information", {
            "fields": ("name", "slug", "location", "description", "is_active")
        }),
        ("Pricing", {
            "fields": ("base_price_per_night", "discount")
        }),
        ("Stats", {
            "fields": ("rating", "review_count"),
            "classes": ("collapse",)
        }),
    )
