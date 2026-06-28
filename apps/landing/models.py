from django.db import models
from django.conf import settings


class LandingPageContent(models.Model):
    """
    Model to store configurable landing page content.
    Allows admins to edit hero, features, steps, and educator section.
    """
    section = models.CharField(
        max_length=50,
        unique=True,
        choices=[
            ('hero', 'Hero Section'),
            ('statistics', 'Statistics Section'),
            ('features', 'Features Section'),
            ('steps', 'How It Works Steps'),
            ('educator', 'Educator Section'),
            ('announcement', 'Announcement Banner'),
        ]
    )

    # Hero section fields
    hero_title = models.CharField(
        max_length=255,
        blank=True,
        default="Create. Challenge. Learn."
    )
    hero_subtitle = models.TextField(
        blank=True,
        default="Create engaging quizzes, challenge your audience, and track learning outcomes."
    )
    primary_button_text = models.CharField(
        max_length=100,
        blank=True,
        default="Get Started Free"
    )
    secondary_button_text = models.CharField(
        max_length=100,
        blank=True,
        default="See How It Works"
    )

    # Announcement
    announcement_text = models.TextField(blank=True)
    announcement_active = models.BooleanField(default=False)

    # Visibility
    is_visible = models.BooleanField(default=True)

    # Order for features/steps
    order = models.PositiveIntegerField(default=0)

    # JSON field for flexible content (features, steps, etc.)
    content_json = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON content for features, steps, etc."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'section']
        verbose_name = 'Landing Page Content'
        verbose_name_plural = 'Landing Page Contents'

    def __str__(self):
        return self.section


class Feature(models.Model):
    """Individual feature items for the landing page."""
    title = models.CharField(max_length=255)
    description = models.TextField()
    icon = models.CharField(
        max_length=50,
        help_text="Icon class name (e.g., 'fas fa-star')"
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'Feature'
        verbose_name_plural = 'Features'

    def __str__(self):
        return self.title


class Step(models.Model):
    """Step items for 'How It Works' section."""
    title = models.CharField(max_length=255)
    description = models.TextField()
    step_number = models.PositiveIntegerField()
    icon = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['step_number']
        verbose_name = 'Step'
        verbose_name_plural = 'Steps'

    def __str__(self):
        return f"Step {self.step_number}: {self.title}"


class FAQ(models.Model):
    """Frequently Asked Questions for the landing page."""
    question = models.CharField(max_length=500)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'

    def __str__(self):
        return self.question[:50]


class Testimonial(models.Model):
    """Testimonials from users."""
    name = models.CharField(max_length=255)
    designation = models.CharField(max_length=255, blank=True)
    company = models.CharField(max_length=255, blank=True)
    comment = models.TextField()
    rating = models.PositiveIntegerField(
        default=5,
        choices=[(i, i) for i in range(1, 6)]
    )
    avatar = models.ImageField(
        upload_to='testimonials/',
        blank=True,
        null=True
    )
    avatar_url = models.URLField(
        blank=True,
        help_text="URL to avatar image (alternative to upload)"
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'Testimonial'
        verbose_name_plural = 'Testimonials'

    def __str__(self):
        return f"{self.name} - {self.rating}★"


class NewsletterSubscriber(models.Model):
    """Newsletter subscription model."""
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = 'Newsletter Subscriber'
        verbose_name_plural = 'Newsletter Subscribers'
        ordering = ['-created_at']

    def __str__(self):
        return self.email


class ContactMessage(models.Model):
    """Contact form messages."""
    STATUS_CHOICES = [
        ('new', 'New'),
        ('read', 'Read'),
        ('replied', 'Replied'),
        ('archived', 'Archived'),
    ]

    name = models.CharField(max_length=255)
    email = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new'
    )

    class Meta:
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.subject}"


class PlatformStatistics(models.Model):
    """
    Cached platform statistics to avoid expensive queries.
    Auto-updated via management command or signal.
    """
    total_users = models.PositiveIntegerField(default=0)
    total_quizzes = models.PositiveIntegerField(default=0)
    total_questions = models.PositiveIntegerField(default=0)
    total_attempts = models.PositiveIntegerField(default=0)
    average_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    active_users_30d = models.PositiveIntegerField(default=0)

    # JSON fields for complex data
    top_categories = models.JSONField(default=list)
    most_active_users = models.JSONField(default=list)
    newest_quizzes = models.JSONField(default=list)

    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Platform Statistics'
        verbose_name_plural = 'Platform Statistics'

    def __str__(self):
        return f"Statistics (updated: {self.last_updated})"

    @classmethod
    def get_current(cls):
        """Get or create the current statistics instance."""
        stats, _ = cls.objects.get_or_create(pk=1)
        return stats