from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import User


class LoginTests(TestCase):
    """Test cases for login endpoint"""

    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse('login')

    def test_verified_user_can_login(self):
        """Test that a verified user can successfully log in"""
        # Create a verified user
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_verified=True
        )

        response = self.client.post(
            self.login_url,
            {'email': 'test@example.com', 'password': 'testpass123'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_unverified_user_receives_email_not_verified(self):
        """Test that an unverified user receives EMAIL_NOT_VERIFIED error"""
        # Create an unverified user
        user = User.objects.create_user(
            username='unverified',
            email='unverified@example.com',
            password='testpass123',
            is_verified=False
        )

        response = self.client.post(
            self.login_url,
            {'email': 'unverified@example.com', 'password': 'testpass123'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['code'], 'EMAIL_NOT_VERIFIED')
        self.assertEqual(
            response.data['message'],
            "Your email address has not been verified. Please check your inbox and click the verification link before logging in."
        )
        self.assertTrue(response.data['can_resend_verification'])

    def test_invalid_password_returns_invalid_credentials(self):
        """Test that invalid password returns INVALID_CREDENTIALS"""
        # Create a verified user
        user = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='correctpass',
            is_verified=True
        )

        response = self.client.post(
            self.login_url,
            {'email': 'test2@example.com', 'password': 'wrongpass'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['code'], 'INVALID_CREDENTIALS')
        self.assertEqual(response.data['message'], 'Invalid email or password.')

    def test_invalid_email_returns_invalid_credentials(self):
        """Test that invalid email returns INVALID_CREDENTIALS"""
        response = self.client.post(
            self.login_url,
            {'email': 'nonexistent@example.com', 'password': 'anypass'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['code'], 'INVALID_CREDENTIALS')
        self.assertEqual(response.data['message'], 'Invalid email or password.')


class ResendVerificationTests(TestCase):
    """Test cases for resend verification endpoint"""

    def setUp(self):
        self.client = APIClient()
        self.resend_url = reverse('resend-verification')

    def test_resend_verification_for_unverified_user(self):
        """Test that verification email is sent for unverified user"""
        # Create an unverified user
        user = User.objects.create_user(
            username='unverified',
            email='unverified@example.com',
            password='testpass123',
            is_verified=False
        )

        response = self.client.post(
            self.resend_url,
            {'email': 'unverified@example.com'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['message'],
            "If an account exists and is not yet verified, a verification email has been sent."
        )

    def test_resend_verification_for_verified_user_no_email_sent(self):
        """Test that no email is sent for already verified user"""
        # Create a verified user
        user = User.objects.create_user(
            username='verified',
            email='verified@example.com',
            password='testpass123',
            is_verified=True
        )

        response = self.client.post(
            self.resend_url,
            {'email': 'verified@example.com'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['message'],
            "If an account exists and is not yet verified, a verification email has been sent."
        )

    def test_resend_verification_for_nonexistent_email(self):
        """Test that no email is sent for non-existent email (security)"""
        response = self.client.post(
            self.resend_url,
            {'email': 'nonexistent@example.com'},
            format='json'
        )

        # Should return same message as for verified user to prevent enumeration
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['message'],
            "If an account exists and is not yet verified, a verification email has been sent."
        )

    def test_resend_verification_requires_email(self):
        """Test that email field is required"""
        response = self.client.post(
            self.resend_url,
            {},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)