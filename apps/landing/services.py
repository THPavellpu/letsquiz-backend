"""
Business logic services for the landing app.
"""
import uuid
import hashlib
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.db import models


def generate_verification_token(email: str) -> str:
    """Generate a unique verification token for newsletter subscription."""
    return hashlib.sha256(
        f"{email}{uuid.uuid4()}{settings.SECRET_KEY}".encode()
    ).hexdigest()


def send_newsletter_verification_email(email: str, token: str) -> bool:
    """
    Send verification email for newsletter subscription.

    Returns:
        bool: True if email was sent successfully
    """
    try:
        verification_url = f"{settings.FRONTEND_URL}/newsletter/verify?token={token}"

        subject = "Verify your LetsQuiz Newsletter Subscription"
        message = f"""
        Welcome to LetsQuiz!

        Thank you for subscribing to our newsletter. Please verify your email by clicking the link below:

        {verification_url}

        If you didn't request this, please ignore this email.

        Best regards,
        The LetsQuiz Team
        """

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_FROM,
            recipient_list=[email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        # Log error in production
        print(f"Failed to send newsletter verification email: {e}")
        return False


def send_contact_notification_to_admin(message_id: int, name: str, email: str) -> bool:
    """
    Send notification to admin about new contact message.

    Returns:
        bool: True if notification was sent
    """
    try:
        admin_email = settings.EMAIL_FROM.split('<')[1].rstrip('>') if '<' in settings.EMAIL_FROM else settings.EMAIL_FROM

        subject = f"New Contact Form Submission from {name}"
        message = f"""
        You have a new contact form submission:

        Name: {name}
        Email: {email}

        Please check the admin panel for the full message.

        View in admin: {settings.FRONTEND_URL}/admin/landing/contactmessage/{message_id}/change/
        """

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_FROM,
            recipient_list=[admin_email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send admin notification: {e}")
        return False


def _compute_average_score_percent(completed_attempts_qs):
    """Compute average quiz score percent across completed attempts.

    Score percent for an attempt is:
      attempt.score / total_quiz_marks * 100

    Assumes attempt.quiz and quiz.questions.marks exist.
    """
    from quizzes.models import Question

    # Compute total marks per quiz to normalize attempt.score
    quiz_marks = (
        Question.objects.values('quiz_id')
        .annotate(total_marks=models.Sum('marks'))
    )
    quiz_marks_map = {
        row['quiz_id']: row['total_marks'] or 0
        for row in quiz_marks
    }

    total_percent_sum = 0.0
    count = 0

    # Select needed fields to avoid N+1s
    for attempt in completed_attempts_qs.select_related('quiz'):
        total_marks = quiz_marks_map.get(attempt.quiz_id, 0)
        if total_marks > 0:
            total_percent_sum += (attempt.score / total_marks) * 100.0
            count += 1

    if count == 0:
        return 0

    return round(total_percent_sum / count, 2)


def calculate_platform_statistics():
    """Calculate platform statistics from database."""
    from django.contrib.auth import get_user_model
    from quizzes.models import Quiz, Question, QuizAttempt

    User = get_user_model()

    total_users = User.objects.count()
    total_quizzes = Quiz.objects.filter(is_active=True).count()
    total_questions = Question.objects.count()

    completed_attempts = QuizAttempt.objects.filter(completed=True)
    total_attempts = completed_attempts.count()

    average_score = _compute_average_score_percent(completed_attempts)

    thirty_days_ago = timezone.now() - timedelta(days=30)
    active_users_30d = User.objects.filter(last_login__gte=thirty_days_ago).count()

    most_active_users = list(
        User.objects.annotate(quiz_count=models.Count('quizzes'))
        .filter(quiz_count__gt=0)
        .order_by('-quiz_count')[:5]
        .values('id', 'username', 'email', 'quiz_count')
    )

    newest_quizzes = list(
        Quiz.objects.filter(is_active=True)
        .order_by('-created_at')[:5]
        .values('id', 'title', 'quiz_code', 'creator__username', 'created_at')
    )

    # Categories are not implemented in the provided quiz models.
    top_categories = []

    return {
        'total_users': total_users,
        'total_quizzes': total_quizzes,
        'total_questions': total_questions,
        'total_attempts': total_attempts,
        'average_score': average_score,
        'active_users_30d': active_users_30d,
        'most_active_users': most_active_users,
        'newest_quizzes': newest_quizzes,
        'top_categories': top_categories,
    }



def refresh_platform_statistics():
    """
    Refresh cached platform statistics.
    """
    from .models import PlatformStatistics

    stats = PlatformStatistics.get_current()
    data = calculate_platform_statistics()

    stats.total_users = data['total_users']
    stats.total_quizzes = data['total_quizzes']
    stats.total_questions = data['total_questions']
    stats.total_attempts = data['total_attempts']
    stats.average_score = data['average_score']
    stats.active_users_30d = data['active_users_30d']
    stats.top_categories = data['top_categories']
    stats.most_active_users = data['most_active_users']
    stats.newest_quizzes = data['newest_quizzes']

    stats.save()
    return stats