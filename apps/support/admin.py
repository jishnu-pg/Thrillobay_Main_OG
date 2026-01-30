from django.contrib import admin
from .models import SupportRequest, SupportTimeline, FAQ, FAQItem


class SupportTimelineInline(admin.TabularInline):
    model = SupportTimeline
    extra = 0
    fields = ('message', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)


class FAQItemInline(admin.StackedInline):
    model = FAQItem
    extra = 1
    fields = ("title", "description", "order")


@admin.register(SupportRequest)
class SupportRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'request_type', 'status', 'created_at', 'updated_at')
    list_filter = ('request_type', 'status', 'created_at', 'updated_at')
    search_fields = ('id', 'booking__id', 'booking__user__username', 'booking__user__email', 'request_type')
    raw_id_fields = ('booking',)
    inlines = [SupportTimelineInline]
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(SupportTimeline)
class SupportTimelineAdmin(admin.ModelAdmin):
    list_display = ('id', 'support_request', 'message', 'created_at')
    list_filter = ('created_at', 'updated_at', 'support_request__status')
    search_fields = ('message', 'support_request__id', 'support_request__booking__id')
    raw_id_fields = ('support_request',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    save_as = True
    list_display = ("id", "location", "question", "is_active")
    list_filter = ("location", "is_active")
    search_fields = ("location", "question")
    inlines = [FAQItemInline]
    ordering = ("location", "question")
    readonly_fields = ("created_at", "updated_at")


@admin.register(FAQItem)
class FAQItemAdmin(admin.ModelAdmin):
    list_display = ("id", "faq", "title", "order")
    list_filter = ("faq__location", "faq")
    search_fields = ("title", "description")
    ordering = ("faq", "order")
