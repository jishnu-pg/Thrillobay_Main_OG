from django.contrib import admin
from .models import Traveller


@admin.register(Traveller)
class TravellerAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'user', 'email', 'phone', 'gender', 'dob', 'passport_number', 'created_at')
    list_filter = ('gender', 'created_at', 'updated_at')
    search_fields = ('first_name', 'last_name', 'email', 'phone', 'passport_number', 'user__username', 'user__email')
    raw_id_fields = ('user',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
