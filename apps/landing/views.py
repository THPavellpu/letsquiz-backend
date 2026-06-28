from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAdminUser,
)
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

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
from .serializers import (
    LandingPageSerializer,
    LandingPageContentSerializer,
    FeatureSerializer,
    StepSerializer,
    FAQSerializer,
    TestimonialSerializer,
    NewsletterSubscriberSerializer,
    ContactMessageSerializer,
    ContactMessageCreateSerializer,
    PlatformStatisticsSerializer,
)
from .permissions import IsAdminOrReadOnly, IsAdminOnly
from .services import (
    generate_verification_token,
    send_newsletter_verification_email,
    send_contact_notification_to_admin,
    calculate_platform_statistics,
    refresh_platform_statistics,
)


# ==========================================
# Throttle Classes
# ==========================================

class NewsletterRateThrottle(AnonRateThrottle):
    """Rate limiting for newsletter subscription."""
    rate = '5/hour'


class ContactRateThrottle(AnonRateThrottle):
    """Rate limiting for contact form."""
    rate = '3/hour'


# ==========================================
# Landing Page API
# ==========================================

class LandingPageView(APIView):
    """
    GET /api/landing/

    Returns the complete landing page content including:
    - Hero section
    - Statistics (calculated dynamically)
    - Features
    - Steps (How It Works)
    - Educator section
    - Testimonials
    - FAQs
    - Announcement

    Cached for 5 minutes to improve performance.
    """
    permission_classes = [AllowAny]
    throttle_classes = []

    def get(self, request):
        # Try to get from cache
        cache_key = 'landing_page_content'
        cached_data = cache.get(cache_key)

        if cached_data is not None:
            return Response(cached_data)

        # Generate landing page content
        serializer = LandingPageSerializer({})
        data = serializer.data

        # Cache for 5 minutes
        cache.set(cache_key, data, 300)

        return Response(data)


# ==========================================
# Statistics API
# ==========================================

class StatisticsView(APIView):
    """GET /api/statistics/

    Spec fields:
    - active_users
    - total_quizzes
    - total_questions
    - completed_quiz_attempts
    - average_score
    - total_creators
    - total_students
    """

    permission_classes = [AllowAny]

    def get(self, request):
        from django.contrib.auth import get_user_model
        from quizzes.models import Quiz, Question, QuizAttempt

        User = get_user_model()

        # Active users (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        active_users = User.objects.filter(last_login__gte=thirty_days_ago).count()

        total_quizzes = Quiz.objects.filter(is_active=True).count()
        total_questions = Question.objects.count()

        completed_attempts_qs = QuizAttempt.objects.filter(completed=True)
        completed_quiz_attempts = completed_attempts_qs.count()

        # Average score percent across completed attempts
        stats = calculate_platform_statistics()
        average_score = stats.get('average_score', 0)

        # Creators: distinct quiz creators
        total_creators = Quiz.objects.values('creator_id').distinct().count()

        # Students: distinct users with at least one completed attempt
        total_students = completed_attempts_qs.values('user_id').distinct().count()

        return Response({
            'active_users': active_users,
            'total_quizzes': total_quizzes,
            'total_questions': total_questions,
            'completed_quiz_attempts': completed_quiz_attempts,
            'average_score': average_score,
            'total_creators': total_creators,
            'total_students': total_students,
        })



# ==========================================
# Platform Statistics API
# ==========================================

class PlatformStatisticsView(APIView):
    """
    GET /api/platform/statistics/

    Returns detailed platform statistics:
    - Total Users, Quizzes, Questions, Attempts
    - Average Quiz Score
    - Top Categories
    - Most Active Users
    - Newest Quizzes
    """
    permission_classes = [AllowAny]

    def get(self, request):
        # Try to get cached statistics
        cache_key = 'platform_statistics'
        cached_stats = cache.get(cache_key)

        if cached_stats is not None:
            return Response(cached_stats)

        # Get or refresh statistics
        stats = PlatformStatistics.get_current()

        # Check if we need to refresh (older than 1 hour)
        if not stats.last_updated or \
           (timezone.now() - stats.last_updated).total_seconds() > 3600:
            try:
                stats = refresh_platform_statistics()
            except Exception:
                # If refresh fails, use cached data
                pass

        serializer = PlatformStatisticsSerializer(stats)
        data = serializer.data

        # Cache for 15 minutes
        cache.set(cache_key, data, 900)

        return Response(data)

    def post(self, request):
        """
        POST /api/platform/statistics/refresh/

        Manually refresh platform statistics (admin only).
        """
        if not request.user.is_staff:
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            stats = refresh_platform_statistics()
            serializer = PlatformStatisticsSerializer(stats)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ==========================================
# FAQ API
# ==========================================

class FAQListView(APIView):
    """
    GET /api/faqs/

    Returns list of active FAQs ordered by position.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        faqs = FAQ.objects.filter(is_active=True).order_by('order')
        serializer = FAQSerializer(faqs, many=True)
        return Response(serializer.data)


class FAQManageView(generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/faqs/manage/
    POST /api/faqs/manage/
    GET /api/faqs/manage/{id}/
    PUT /api/faqs/manage/{id}/
    DELETE /api/faqs/manage/{id}/

    Admin-only FAQ management.
    """
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return FAQ.objects.all()


# ==========================================
# Testimonials API
# ==========================================

class TestimonialListView(APIView):
    """
    GET /api/testimonials/

    Returns list of active testimonials ordered by position.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        testimonials = Testimonial.objects.filter(is_active=True).order_by('order')
        serializer = TestimonialSerializer(testimonials, many=True)
        return Response(serializer.data)


class TestimonialManageView(generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/testimonials/manage/
    POST /api/testimonials/manage/
    GET /api/testimonials/manage/{id}/
    PUT /api/testimonials/manage/{id}/
    DELETE /api/testimonials/manage/{id}/

    Admin-only testimonial management.
    """
    queryset = Testimonial.objects.all()
    serializer_class = TestimonialSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return Testimonial.objects.all()


# ==========================================
# Newsletter API
# ==========================================

class NewsletterSubscribeView(APIView):
    """
    POST /api/newsletter/

    Subscribe to newsletter with email verification.
    Rate limited: 5 requests per hour per IP.
    """
    permission_classes = [AllowAny]
    throttle_classes = [NewsletterRateThrottle]

    def post(self, request):
        email = request.data.get('email')

        if not email:
            return Response(
                {'error': 'Email is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check for duplicate
        if NewsletterSubscriber.objects.filter(email=email.lower()).exists():
            return Response(
                {'message': 'This email is already subscribed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create subscriber with verification token
        token = generate_verification_token(email)
        subscriber = NewsletterSubscriber.objects.create(
            email=email.lower(),
            verification_token=token
        )

        # Send verification email
        send_newsletter_verification_email(email, token)

        return Response(
            {
                'message': 'Verification email sent. Please check your inbox.',
                'email': email
            },
            status=status.HTTP_201_CREATED
        )


class NewsletterVerifyView(APIView):
    """
    POST /api/newsletter/verify/

    Verify newsletter subscription with token.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('token')

        if not token:
            return Response(
                {'error': 'Token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            subscriber = NewsletterSubscriber.objects.get(verification_token=token)
            subscriber.is_verified = True
            subscriber.verification_token = ''
            subscriber.save()

            return Response({
                'message': 'Newsletter subscription verified successfully!'
            })
        except NewsletterSubscriber.DoesNotExist:
            return Response(
                {'error': 'Invalid verification token'},
                status=status.HTTP_404_NOT_FOUND
            )


# ==========================================
# Contact Form API
# ==========================================

class ContactView(APIView):
    """
    POST /api/contact/

    Submit contact form message.
    Rate limited: 3 requests per hour per IP.
    """
    permission_classes = [AllowAny]
    throttle_classes = [ContactRateThrottle]

    def post(self, request):
        serializer = ContactMessageCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        # Save the message
        message = serializer.save()

        # Send notification to admin
        send_contact_notification_to_admin(
            message.id,
            message.name,
            message.email
        )

        return Response(
            {
                'message': 'Thank you for your message! We will get back to you soon.',
                'id': message.id
            },
            status=status.HTTP_201_CREATED
        )


class ContactManageView(generics.ListAPIView):
    """
    GET /api/contact/manage/

    Admin-only: List all contact messages.
    """
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = ContactMessage.objects.all()

        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset


class ContactDetailView(generics.RetrieveUpdateAPIView):
    """
    GET /api/contact/manage/{id}/
    PATCH /api/contact/manage/{id}/

    Admin-only: View and update contact message status.
    """
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    permission_classes = [IsAdminUser]


# ==========================================
# Landing Content Management API
# ==========================================

class LandingContentView(generics.ListCreateAPIView):
    """
    GET /api/landing/manage/
    POST /api/landing/manage/

    Admin-only: Manage landing page content sections.
    """
    queryset = LandingPageContent.objects.all()
    serializer_class = LandingPageContentSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return LandingPageContent.objects.all()


class LandingContentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/landing/manage/{id}/
    PUT /api/landing/manage/{id}/
    DELETE /api/landing/manage/{id}/

    Admin-only: Manage individual landing page content.
    """
    queryset = LandingPageContent.objects.all()
    serializer_class = LandingPageContentSerializer
    permission_classes = [IsAdminUser]


class FeatureManageView(generics.ListCreateAPIView):
    """
    GET /api/landing/features/manage/
    POST /api/landing/features/manage/

    Admin-only: Manage features.
    """
    queryset = Feature.objects.all()
    serializer_class = FeatureSerializer
    permission_classes = [IsAdminUser]


class FeatureDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/landing/features/manage/{id}/
    PUT /api/landing/features/manage/{id}/
    DELETE /api/landing/features/manage/{id}/

    Admin-only: Manage individual feature.
    """
    queryset = Feature.objects.all()
    serializer_class = FeatureSerializer
    permission_classes = [IsAdminUser]


class StepManageView(generics.ListCreateAPIView):
    """
    GET /api/landing/steps/manage/
    POST /api/landing/steps/manage/

    Admin-only: Manage steps.
    """
    queryset = Step.objects.all()
    serializer_class = StepSerializer
    permission_classes = [IsAdminUser]


class StepDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/landing/steps/manage/{id}/
    PUT /api/landing/steps/manage/{id}/
    DELETE /api/landing/steps/manage/{id}/

    Admin-only: Manage individual step.
    """
    queryset = Step.objects.all()
    serializer_class = StepSerializer
    permission_classes = [IsAdminUser]


# ==========================================
# Cache Management
# ==========================================

class ClearCacheView(APIView):
    """
    POST /api/landing/clear-cache/

    Clear landing page caches (admin only).
    """
    permission_classes = [IsAdminUser]

    def post(self, request):
        cache.delete('landing_page_content')
        cache.delete('platform_statistics')

        return Response({'message': 'Cache cleared successfully'})