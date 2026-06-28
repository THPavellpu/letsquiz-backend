from django.contrib import admin
from .models import (
    LandingPageContent,
    Feature,
    Step,
    FAQ,
    Testimonial,
    NewsletterSubscriber,
    ContactMessage,
    PlatformStatistics,
)


@admin.register(LandingPageContent)
class LandingPageContentAdmin(admin.ModelAdmin):
    """Admin configuration for LandingPageContent."""
    list_display = ['section', 'is_visible', 'order', 'updated_at']
    list_filter = ['section', 'is_visible']
    search_fields = ['section', 'hero_title']
    ordering = ['order', 'section']
    fieldsets = (
        ('Section Info', {
            'fields': ('section', 'is_visible', 'order')
        }),
        ('Hero Section', {
            'fields': ('hero_title', 'hero_subtitle', 'primary_button_text', 'secondary_button_text'),
            'classes': ('collapse',),
        }),
        ('Announcement', {
            'fields': ('announcement_text', 'announcement_active'),
            'classes': ('collapse',),
        }),
        ('Additional Content', {
            'fields': ('content_json',),
            'classes': ('collapse',),
        }),
    )


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    """Admin configuration for Feature."""
    list_display = ['title', 'icon', 'order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['title', 'description']
    ordering = ['order']


@admin.register(Step)
class StepAdmin(admin.ModelAdmin):
    """Admin configuration for Step."""
    list_display = ['step_number', 'title', 'is_active']
    list_filter = ['is_active']
    search_fields = ['title', 'description']
    ordering = ['step_number']


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    """Admin configuration for FAQ."""
    list_display = ['question', 'order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['question', 'answer']
    ordering = ['order']


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    """Admin configuration for Testimonial."""
    list_display = ['name', 'designation', 'rating', 'order', 'is_active']
    list_filter = ['is_active', 'rating']
    search_fields = ['name', 'comment']
    ordering = ['order']


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    """Admin configuration for NewsletterSubscriber."""
    list_display = ['email', 'is_verified', 'created_at']
    list_filter = ['is_verified']
    search_fields = ['email']
    readonly_fields = ['email', 'created_at', 'verification_token']
    ordering = ['-created_at']


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    """Admin configuration for ContactMessage."""
    list_display = ['name', 'email', 'subject', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    readonly_fields = ['name', 'email', 'subject', 'message', 'created_at']
    ordering = ['-created_at']

    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email')
        }),
        ('Message', {
            'fields': ('subject', 'message')
        }),
        ('Status', {
            'fields': ('status', 'created_at')
        }),
    )


@admin.register(PlatformStatistics)
class PlatformStatisticsAdmin(admin.ModelAdmin):
    """Admin configuration for PlatformStatistics."""
    list_display = ['__str__', 'last_updated']
    readonly_fields = [
        'total_users', 'total_quizzes', 'total_questions',
        'total_attempts', 'average_score', 'active_users_30d',
        'top_categories', 'most_active_users', 'newest_quizzes',
        'last_updated'
    ]

    def has_add_permission(self, request):
        # Prevent adding new statistics records
        return False

    def has_delete_permission(self, request, obj=None):
        # Prevent deleting statistics
        return False