"""
Tests for the Landing app.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock

from .models import (
    LandingPageContent,
    Feature,
    Step,
    FAQ,
    Testimonial,
    NewsletterSubscriber,
    ContactMessage,
)

User = get_user_model()


class LandingPageTests(APITestCase):
    """Test cases for Landing Page API."""

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/landing/'

    def test_landing_page_returns_200(self):
        """Test that landing page returns 200 OK."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_landing_page_contains_hero_section(self):
        """Test that landing page contains hero section."""
        response = self.client.get(self.url)
        self.assertIn('hero', response.data)
        self.assertIn('title', response.data['hero'])

    def test_landing_page_contains_statistics(self):
        """Test that landing page contains statistics."""
        response = self.client.get(self.url)
        self.assertIn('statistics', response.data)
        self.assertIn('active_users', response.data['statistics'])

    def test_landing_page_contains_features(self):
        """Test that landing page contains features."""
        response = self.client.get(self.url)
        self.assertIn('features', response.data)

    def test_landing_page_contains_steps(self):
        """Test that landing page contains steps."""
        response = self.client.get(self.url)
        self.assertIn('steps', response.data)


class StatisticsTests(APITestCase):
    """Test cases for Statistics API."""

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/statistics/'

    def test_statistics_returns_200(self):
        """Test that statistics returns 200 OK."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_statistics_contains_required_fields(self):
        """Test that statistics contains all required fields."""
        response = self.client.get(self.url)
        required_fields = [
            'active_users', 'quizzes_created', 'questions_answered',
            'total_questions', 'average_score'
        ]
        for field in required_fields:
            self.assertIn(field, response.data)


class FAQTests(APITestCase):
    """Test cases for FAQ API."""

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/faqs/'

    def test_faq_list_returns_200(self):
        """Test that FAQ list returns 200 OK."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_faq_list_returns_empty_for_no_faqs(self):
        """Test that FAQ list returns empty list when no FAQs exist."""
        response = self.client.get(self.url)
        self.assertEqual(response.data, [])

    def test_faq_list_returns_active_faqs(self):
        """Test that FAQ list only returns active FAQs."""
        # Create active and inactive FAQs
        FAQ.objects.create(
            question="Active Question?",
            answer="Active Answer",
            is_active=True,
            order=1
        )
        FAQ.objects.create(
            question="Inactive Question?",
            answer="Inactive Answer",
            is_active=False,
            order=2
        )

        response = self.client.get(self.url)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['question'], "Active Question?")


class TestimonialTests(APITestCase):
    """Test cases for Testimonial API."""

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/testimonials/'

    def test_testimonial_list_returns_200(self):
        """Test that testimonial list returns 200 OK."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_testimonial_list_returns_active_only(self):
        """Test that testimonial list only returns active testimonials."""
        Testimonial.objects.create(
            name="John Doe",
            comment="Great platform!",
            is_active=True,
            order=1
        )
        Testimonial.objects.create(
            name="Jane Doe",
            comment="Not so great",
            is_active=False,
            order=2
        )

        response = self.client.get(self.url)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "John Doe")


class NewsletterTests(APITestCase):
    """Test cases for Newsletter API."""

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/newsletter/'

    def test_newsletter_subscribe_returns_201(self):
        """Test that newsletter subscription returns 201."""
        response = self.client.post(self.url, {'email': 'test@example.com'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_newsletter_subscribe_fails_without_email(self):
        """Test that newsletter subscription fails without email."""
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_newsletter_subscribe_fails_with_invalid_email(self):
        """Test that newsletter subscription fails with invalid email."""
        response = self.client.post(self.url, {'email': 'invalid-email'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_newsletter_subscribe_fails_with_duplicate(self):
        """Test that duplicate subscription fails."""
        NewsletterSubscriber.objects.create(email='test@example.com')
        response = self.client.post(self.url, {'email': 'test@example.com'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('apps.landing.views.send_newsletter_verification_email')
    def test_newsletter_sends_verification_email(self, mock_send_email):
        """Test that verification email is sent on subscription."""
        mock_send_email.return_value = True
        response = self.client.post(self.url, {'email': 'new@example.com'})
        self.assertTrue(mock_send_email.called)


class ContactTests(APITestCase):
    """Test cases for Contact Form API."""

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/contact/'

    def test_contact_submission_returns_201(self):
        """Test that contact submission returns 201."""
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'subject': 'Test Subject',
            'message': 'This is a test message with enough characters.'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_contact_submission_fails_without_required_fields(self):
        """Test that contact submission fails without required fields."""
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_contact_submission_fails_with_short_message(self):
        """Test that contact submission fails with short message."""
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'subject': 'Test Subject',
            'message': 'Short'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AdminTests(APITestCase):
    """Test cases for Admin API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.client.force_authenticate(user=self.admin_user)

    def test_faq_manage_list_returns_200(self):
        """Test that FAQ management list returns 200 for admin."""
        response = self.client.get('/api/faqs/manage/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_faq_create_returns_201(self):
        """Test that FAQ creation returns 201."""
        data = {
            'question': 'Test Question?',
            'answer': 'Test Answer',
            'order': 1,
            'is_active': True
        }
        response = self.client.post('/api/faqs/manage/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_testimonial_manage_returns_200(self):
        """Test that testimonial management returns 200 for admin."""
        response = self.client.get('/api/testimonials/manage/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthorized_access_returns_403(self):
        """Test that unauthorized access returns 403."""
        # Create a regular user
        regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='userpass123'
        )
        self.client.force_authenticate(user=regular_user)

        response = self.client.get('/api/faqs/manage/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ModelTests(TestCase):
    """Test cases for Landing app models."""

    def test_faq_str(self):
        """Test FAQ string representation."""
        faq = FAQ.objects.create(
            question="What is LetsQuiz?",
            answer="It is a quiz platform."
        )
        self.assertEqual(str(faq), "What is LetsQuiz?")

    def test_testimonial_str(self):
        """Test Testimonial string representation."""
        testimonial = Testimonial.objects.create(
            name="John Doe",
            rating=5
        )
        self.assertEqual(str(testimonial), "John Doe - 5★")

    def test_contact_message_default_status(self):
        """Test that contact message has default status."""
        message = ContactMessage.objects.create(
            name="John",
            email="john@example.com",
            subject="Test",
            message="Test message content here."
        )
        self.assertEqual(message.status, 'new')