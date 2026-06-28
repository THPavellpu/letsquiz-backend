from rest_framework import serializers
from django.contrib.auth import get_user_model
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

User = get_user_model()


class FeatureSerializer(serializers.ModelSerializer):
    """Serializer for Feature model."""

    class Meta:
        model = Feature
        fields = ['id', 'title', 'description', 'icon', 'order', 'is_active']


class StepSerializer(serializers.ModelSerializer):
    """Serializer for Step model."""

    class Meta:
        model = Step
        fields = ['id', 'title', 'description', 'step_number', 'icon', 'is_active']


class FAQSerializer(serializers.ModelSerializer):
    """Serializer for FAQ model."""

    class Meta:
        model = FAQ
        fields = ['id', 'question', 'answer', 'order', 'is_active']


class TestimonialSerializer(serializers.ModelSerializer):
    """Serializer for Testimonial model."""

    class Meta:
        model = Testimonial
        fields = [
            'id', 'name', 'designation', 'company', 'comment',
            'rating', 'avatar', 'avatar_url', 'order', 'is_active'
        ]

    def to_representation(self, instance):
        """Customize avatar output to return URL."""
        data = super().to_representation(instance)
        if instance.avatar:
            data['avatar'] = instance.avatar.url
        elif instance.avatar_url:
            data['avatar'] = instance.avatar_url
        else:
            data['avatar'] = None
        return data


class LandingPageContentSerializer(serializers.ModelSerializer):
    """Serializer for LandingPageContent model."""
    features = FeatureSerializer(many=True, read_only=True)
    steps = StepSerializer(many=True, read_only=True)

    class Meta:
        model = LandingPageContent
        fields = [
            'id', 'section', 'hero_title', 'hero_subtitle',
            'primary_button_text', 'secondary_button_text',
            'announcement_text', 'announcement_active',
            'is_visible', 'order', 'content_json',
            'features', 'steps',
            'created_at', 'updated_at'
        ]


class NewsletterSubscriberSerializer(serializers.ModelSerializer):
    """Serializer for Newsletter subscription."""

    class Meta:
        model = NewsletterSubscriber
        fields = ['email', 'created_at', 'is_verified']
        read_only_fields = ['created_at', 'is_verified']

    def validate_email(self, value):
        """Validate email format."""
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        try:
            validate_email(value)
        except ValidationError:
            raise serializers.ValidationError("Invalid email format.")
        return value.lower()


class ContactMessageSerializer(serializers.ModelSerializer):
    """Serializer for ContactMessage model."""

    class Meta:
        model = ContactMessage
        fields = ['id', 'name', 'email', 'subject', 'message', 'created_at', 'status']
        read_only_fields = ['id', 'created_at', 'status']


class ContactMessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating ContactMessage."""

    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']

    def validate_email(self, value):
        """Validate email format."""
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        try:
            validate_email(value)
        except ValidationError:
            raise serializers.ValidationError("Invalid email format.")
        return value.lower()

    def validate_message(self, value):
        """Validate message content."""
        if len(value) < 10:
            raise serializers.ValidationError(
                "Message must be at least 10 characters long."
            )
        if len(value) > 5000:
            raise serializers.ValidationError(
                "Message must not exceed 5000 characters."
            )
        return value


class PlatformStatisticsSerializer(serializers.ModelSerializer):
    """Serializer for Platform Statistics."""

    class Meta:
        model = PlatformStatistics
        fields = [
            'total_users', 'total_quizzes', 'total_questions',
            'total_attempts', 'average_score', 'active_users_30d',
            'top_categories', 'most_active_users', 'newest_quizzes',
            'last_updated'
        ]


class LandingPageSerializer(serializers.Serializer):
    """
    Complete landing page serializer combining all sections.
    """
    hero = serializers.SerializerMethodField()
    statistics = serializers.SerializerMethodField()
    features = serializers.SerializerMethodField()
    steps = serializers.SerializerMethodField()
    educator_section = serializers.SerializerMethodField()
    testimonials = serializers.SerializerMethodField()
    faqs = serializers.SerializerMethodField()
    announcement = serializers.SerializerMethodField()

    def get_hero(self, obj):
        """Get hero section content."""
        hero = LandingPageContent.objects.filter(section='hero', is_visible=True).first()
        if hero:
            return {
                'title': hero.hero_title,
                'subtitle': hero.hero_subtitle,
                'primary_button': hero.primary_button_text,
                'secondary_button': hero.secondary_button_text
            }

        # Default hero content
        return {
            'title': 'Create. Challenge. Learn.',
            'subtitle': 'Create engaging quizzes, challenge your audience, and track learning outcomes with LetsQuiz.',
            'primary_button': 'Get Started Free',
            'secondary_button': 'See How It Works'
        }

    def get_statistics(self, obj):
        """Get statistics - calculated dynamically."""
        from quizzes.models import Quiz, Question, QuizAttempt
        from django.contrib.auth import get_user_model

        User = get_user_model()

        active_users = User.objects.filter(is_active=True).count()
        quizzes_created = Quiz.objects.filter(is_active=True).count()
        questions_answered = QuizAttempt.objects.filter(completed=True).count()

        # Calculate average score from completed attempts
        completed_attempts = QuizAttempt.objects.filter(completed=True)
        avg_score = 0
        if completed_attempts.exists():
            total_score = sum(
                attempt.score for attempt in completed_attempts
                if attempt.quiz and hasattr(attempt.quiz, 'questions')
            )
            # Get total possible marks
            total_marks = 0
            for attempt in completed_attempts:
                if attempt.quiz:
                    total_marks += attempt.quiz.questions.count()

            if total_marks > 0:
                avg_score = round((total_score / total_marks) * 100, 1)

        # Map to landing page contract
        return {
            'active_users': active_users,
            'quizzes_created': quizzes_created,
            'questions_answered': questions_answered,
            'satisfaction': 98
        }


    def get_features(self, obj):
        """Get active features."""
        features = Feature.objects.filter(is_active=True).order_by('order')
        return FeatureSerializer(features, many=True).data

    def get_steps(self, obj):
        """Get active steps."""
        steps = Step.objects.filter(is_active=True).order_by('step_number')
        return StepSerializer(steps, many=True).data

    def get_educator_section(self, obj):
        """Get educator section content."""
        educator = LandingPageContent.objects.filter(section='educator', is_visible=True).first()
        if educator:
            return {
                'title': educator.hero_title,
                'description': educator.hero_subtitle,
                'features': educator.content_json.get('features', [])
            }
        # Default educator content
        return {
            'title': 'For Educators',
            'description': 'Empower your teaching with interactive quizzes that engage students and provide instant feedback.',
            'features': [
                'Create quizzes in minutes',
                'Track student progress',
                'Access detailed analytics',
                'Share quizzes easily'
            ]
        }

    def get_testimonials(self, obj):
        """Get active testimonials."""
        testimonials = Testimonial.objects.filter(is_active=True).order_by('order')
        return TestimonialSerializer(testimonials, many=True).data

    def get_faqs(self, obj):
        """Get active FAQs."""
        faqs = FAQ.objects.filter(is_active=True).order_by('order')
        return FAQSerializer(faqs, many=True).data

    def get_announcement(self, obj):
        """Get announcement if active."""
        announcement = LandingPageContent.objects.filter(
            section='announcement',
            announcement_active=True,
            is_visible=True
        ).first()
        if announcement:
            return {
                'text': announcement.announcement_text,
                'active': True
            }
        return {'text': None, 'active': False}