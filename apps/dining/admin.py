from django.contrib import admin
from .models import FoodDestination, FoodDestinationImage

class FoodDestinationImageInline(admin.TabularInline):
    model = FoodDestinationImage
    extra = 1

@admin.register(FoodDestination)
class FoodDestinationAdmin(admin.ModelAdmin):
    save_as = True
    list_display = ("name", "location", "price_per_person", "rating", "is_active")
    list_filter = ("is_active", "location")
    search_fields = ("name", "location")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [FoodDestinationImageInline]
