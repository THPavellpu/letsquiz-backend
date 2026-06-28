from django.urls import path
from . import views

app_name = 'landing'

urlpatterns = [
    # ==========================================
    # Public Endpoints
    # ==========================================

    # Landing Page

    path(
        'landing/',
        views.LandingPageView.as_view(),
        name='landing_page'
    ),

    # Statistics
    path(
        'statistics/',
        views.StatisticsView.as_view(),
        name='statistics'
    ),

    # Platform Statistics
    path(
        'platform/statistics/',
        views.PlatformStatisticsView.as_view(),
        name='platform_statistics'
    ),

    # FAQs
    path(
        'faqs/',
        views.FAQListView.as_view(),
        name='faq_list'
    ),

    # Testimonials
    path(
        'testimonials/',
        views.TestimonialListView.as_view(),
        name='testimonial_list'
    ),

    # Newsletter
    path(
        'newsletter/',
        views.NewsletterSubscribeView.as_view(),
        name='newsletter_subscribe'
    ),
    path(
        'newsletter/verify/',
        views.NewsletterVerifyView.as_view(),
        name='newsletter_verify'
    ),

    # Contact Form
    path(
        'contact/',
        views.ContactView.as_view(),
        name='contact'
    ),

    # ==========================================
    # Admin Management Endpoints
    # ==========================================

    # Landing Content Management
    path(
        'landing/manage/',
        views.LandingContentView.as_view(),
        name='landing_manage_list'
    ),
    path(
        'landing/manage/<int:pk>/',
        views.LandingContentDetailView.as_view(),
        name='landing_manage_detail'
    ),
    path(
        'landing/clear-cache/',
        views.ClearCacheView.as_view(),
        name='clear_cache'
    ),

    # FAQ Management
    path(
        'faqs/manage/',
        views.FAQManageView.as_view(),
        name='faq_manage_list'
    ),
    path(
        'faqs/manage/<int:pk>/',
        views.FAQManageView.as_view(),
        name='faq_manage_detail'
    ),

    # Testimonial Management
    path(
        'testimonials/manage/',
        views.TestimonialManageView.as_view(),
        name='testimonial_manage_list'
    ),
    path(
        'testimonials/manage/<int:pk>/',
        views.TestimonialManageView.as_view(),
        name='testimonial_manage_detail'
    ),

    # Contact Message Management
    path(
        'contact/manage/',
        views.ContactManageView.as_view(),
        name='contact_manage_list'
    ),
    path(
        'contact/manage/<int:pk>/',
        views.ContactDetailView.as_view(),
        name='contact_manage_detail'
    ),

    # Feature Management
    path(
        'landing/features/manage/',
        views.FeatureManageView.as_view(),
        name='feature_manage_list'
    ),
    path(
        'landing/features/manage/<int:pk>/',
        views.FeatureDetailView.as_view(),
        name='feature_manage_detail'
    ),

    # Step Management
    path(
        'landing/steps/manage/',
        views.StepManageView.as_view(),
        name='step_manage_list'
    ),
    path(
        'landing/steps/manage/<int:pk>/',
        views.StepDetailView.as_view(),
        name='step_manage_detail'
    ),
]