from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from django.db.models import Sum
from .models import (
    HolidayPackage, PackageImage, PackageFeature, PackageItinerary,
    PackageAccommodation, PackageActivity, PackageTransfer, PackageInclusion
)

# --- FORMS & VALIDATION ---

class PackageItineraryForm(forms.ModelForm):
    """
    Validation logic for the day-wise itinerary.
    """
    class Meta:
        model = PackageItinerary
        fields = "__all__"
        labels = {
            "from_location": "Start Location",
            "to_location": "End Location",
            "stay_property": "Hotel / Resort",
            "stay_houseboat": "Houseboat Stay",
        }

    def clean(self):
        cleaned_data = super().clean()
        stay_property = cleaned_data.get("stay_property")
        stay_houseboat = cleaned_data.get("stay_houseboat")
        stay_nights = cleaned_data.get("stay_nights", 0)

        # ❌ Guardrail 1: Both stay_property and stay_houseboat selected
        if stay_property and stay_houseboat:
            raise ValidationError(
                "A single day cannot have both a Hotel and a Houseboat stay. Please choose one."
            )

        # ❌ Guardrail 2: Stay nights provided but no accommodation selected
        if stay_nights > 0 and not (stay_property or stay_houseboat):
            raise ValidationError(
                f"You have specified {stay_nights} nights stay, but no Hotel or Houseboat is selected."
            )

        return cleaned_data

# --- INLINES ---

class PackageImageInline(admin.TabularInline):
    model = PackageImage
    extra = 1
    classes = ("collapse",)
    verbose_name = "Gallery Image"
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        if obj.image:
            try:
                return format_html('<img src="{}" width="100" height="auto" />', obj.image.url)
            except:
                return "No image"
        return "No image"

class PackageFeatureInline(admin.TabularInline):
    model = PackageFeature
    extra = 1
    classes = ("collapse",)

class PackageItineraryInline(admin.StackedInline):
    model = PackageItinerary
    form = PackageItineraryForm
    extra = 1
    ordering = ("day_number", "order")
    # Added a clear visual indicator for the day
    template = "admin/edit_inline/stacked.html" 
    
    fieldsets = (
        (None, {
            "fields": (("day_number", "order"), "title", "description")
        }),
        ("Travel & Stay Configuration", {
            "description": "Specify the journey start/end and accommodation for this day.",
            "fields": (
                ("from_location", "to_location"), 
                ("transport_type", "stay_property", "stay_houseboat", "stay_nights")
            )
        }),
    )

class PackageAccommodationInline(admin.TabularInline):
    model = PackageAccommodation
    extra = 0
    autocomplete_fields = ["property", "room_type"]
    classes = ("collapse",)

class PackageActivityInline(admin.TabularInline):
    model = PackageActivity
    extra = 0
    autocomplete_fields = ["activity", "itinerary_day"]

class PackageTransferInline(admin.TabularInline):
    model = PackageTransfer
    extra = 0
    autocomplete_fields = ["cab_category", "itinerary_day"]

class PackageInclusionInline(admin.TabularInline):
    model = PackageInclusion
    extra = 1
    classes = ("collapse",)

# --- MAIN ADMIN ---

@admin.register(HolidayPackage)
class HolidayPackageAdmin(admin.ModelAdmin):
    # Display configuration
    list_display = ("title", "primary_location", "duration_days", "duration_nights", "base_price", "is_active")
    list_filter = ("is_active", "primary_location")
    search_fields = ("title", "primary_location")
    prepopulated_fields = {"slug": ("title",)}
    
    # 1️⃣ Page Structure with Fieldsets
    fieldsets = (
        ("Basic Information", {
            "fields": (
                "title", "slug", "primary_location", "secondary_locations", 
                ("rating", "review_count"), "is_active"
            ),
            "description": "Core identity of the holiday package."
        }),
        ("Duration & Pricing", {
            "fields": (("duration_days", "duration_nights"), ("base_price", "discount")),
        }),
        ("Descriptions & Highlights", {
            "fields": ("short_description", "highlights", "terms_and_conditions"),
            "classes": ("collapse",),
        }),
        ("Package Summary (Internal)", {
            "fields": ("package_summary_display",),
            "classes": ("collapse",),
        }),
    )

    readonly_fields = ("package_summary_display",)

    # Inlines configuration
    inlines = [
        PackageItineraryInline, # Prominent day-wise focus
        PackageActivityInline,
        PackageTransferInline,
        PackageAccommodationInline,
        PackageImageInline, 
        PackageFeatureInline, 
        PackageInclusionInline
    ]

    # 6️⃣ Admin Confidence Boost: Summary Display
    def package_summary_display(self, obj):
        if not obj.pk:
            return "Save the package to see a summary."
        
        itineraries = obj.itinerary.all()
        hotels = [i.stay_property.name for i in itineraries if i.stay_property]
        boats = [i.stay_houseboat.name for i in itineraries if i.stay_houseboat]
        total_stay_nights = itineraries.aggregate(Sum('stay_nights'))['stay_nights__sum'] or 0
        
        summary_html = f"""
            <div style='line-height: 1.6;'>
                <strong>Total Nights allocated in Itinerary:</strong> {total_stay_nights} / {obj.duration_nights}<br>
                <strong>Hotels Used:</strong> {', '.join(hotels) if hotels else 'None'}<br>
                <strong>Houseboats Used:</strong> {', '.join(boats) if boats else 'None'}
            </div>
        """
        return format_html(summary_html)

    package_summary_display.short_description = "Configuration Summary"

    class Media:
        # Subtle CSS to make "DAY X" labels stand out in the StackedInline
        css = {
            'all': ('admin/css/package_custom.css',)
        }

@admin.register(PackageItinerary)
class PackageItineraryAdmin(admin.ModelAdmin):
    list_display = ("package", "day_number", "title")
    list_filter = ("day_number", "package__primary_location")
    search_fields = ("title", "day_number", "package__title")  # REQUIRED for autocomplete
    raw_id_fields = ("package", "stay_property", "stay_houseboat")

@admin.register(PackageActivity)
class PackageActivityAdmin(admin.ModelAdmin):
    list_display = ("name", "package", "itinerary_day")
    search_fields = ("name", "package__title")
    raw_id_fields = ("package", "itinerary_day")

@admin.register(PackageTransfer)
class PackageTransferAdmin(admin.ModelAdmin):
    list_display = ("transport_type", "package", "itinerary_day")
    search_fields = ("transport_type", "package__title")
    raw_id_fields = ("package", "itinerary_day")

