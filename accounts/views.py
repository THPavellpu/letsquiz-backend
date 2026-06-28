from rest_framework import generics
from .models import User
from .serializers import RegisterSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import EmailTokenObtainPairSerializer
from django.shortcuts import get_object_or_404
from django.utils.http import urlsafe_base64_decode
from rest_framework import status
from .tokens import email_verification_token
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from .serializers import ForgotPasswordSerializer
from .serializers import ResetPasswordSerializer
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.hashers import check_password
from django.shortcuts import redirect
from django.conf import settings
from .serializers import ChangePasswordSerializer
from .serializers import ProfileStatsSerializer
from quizzes.models import Quiz, QuizAttempt


class RegisterView(generics.CreateAPIView):

    queryset = User.objects.all()
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        print("=== REGISTER VIEW REACHED ===")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        uidb64 = urlsafe_base64_encode(
            force_bytes(user.id)
        )

        token = email_verification_token.make_token(user)

        # Build verification URL dynamically (works across deployments).
        # accounts/urls.py already defines: verify-email/<uidb64>/<token>/
        verification_link = request.build_absolute_uri(
            f"/api/auth/verify-email/{uidb64}/{token}/"
        )

        import logging
        logger = logging.getLogger(__name__)

        logger.info(
            "Verification URL generated",
            extra={"username": user.username, "verification_url": verification_link},
        )

        # Attempt to send verification email; registration must not crash.
        try:
            from quizzes.email_service import send_verification_email

            logger.info("About to call send_verification_email")
            print("=== BEFORE EMAIL ===")

            send_verification_email(
                user_email=user.email,
                username=user.username,
                verification_link=verification_link,
            )
            print("=== AFTER EMAIL ===")

            logger.info("send_verification_email finished")

            logger.info(
                "Email sent successfully",
                extra={"recipient": user.email, "username": user.username, "verification_url": verification_link},
            )

            return Response({
                "message": "Registration successful. Please check your email to verify your account."
            })
        except Exception as e:
            # Log full error details but never crash the registration endpoint.
            logger.exception(
                "Resend API errors: Failed to send verification email",
                extra={
                    "recipient": user.email,
                    "username": user.username,
                    "verification_url": verification_link,
                    "exception": str(e),
                },
            )

            return Response({
                "message": "Registration completed but verification email could not be sent."
            })


class ProfileView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        return Response({
            "id": request.user.id,
            "username": request.user.username,
            "email": request.user.email,
            
            "is_verified": request.user.is_verified
        })  
class EmailLoginView(TokenObtainPairView):

    serializer_class = EmailTokenObtainPairSerializer
class VerifyEmailView(APIView):

    def get(self, request, uidb64, token):
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')

        try:
            user_id = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=user_id)

        except Exception:
            return redirect(f"{frontend_url}/verify-failed?reason=invalid")

        if user.is_verified:
            return redirect(f"{frontend_url}/verify-failed?reason=already_verified")

        if email_verification_token.check_token(user, token):
            user.is_verified = True
            user.save()
            return redirect(f"{frontend_url}/verify-success")

        return redirect(f"{frontend_url}/verify-failed?reason=expired")
class ForgotPasswordView(APIView):

    def post(self, request):
        import logging
        logger = logging.getLogger(__name__)

        logger.info("Forgot password request received")

        serializer = ForgotPasswordSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        logger.info(f"Looking up user with email: {email}")

        try:
            user = User.objects.get(email=email)

        except User.DoesNotExist:
            logger.warning(f"User not found for email: {email}")
            # Return the same message whether user exists or not (security best practice)
            return Response({
                "message": "If an account with this email exists, a password reset link has been sent."
            })

        logger.info(f"User found: {user.username}")

        uidb64 = urlsafe_base64_encode(
            force_bytes(user.id)
        )

        logger.info("Generating password reset token")

        token = email_verification_token.make_token(
            user
        )

        # Use FRONTEND_URL for the reset link (not backend URL)
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        reset_link = (
            f"{frontend_url}/reset-password/"
            f"{uidb64}/{token}/"
        )

        logger.info(f"Reset URL generated: {reset_link}")

        # Send the password reset email
        try:
            from quizzes.email_service import send_password_reset_email

            logger.info("Calling send_password_reset_email")

            send_password_reset_email(
                user_email=user.email,
                username=user.username,
                reset_link=reset_link,
            )

            logger.info("Password reset email sent successfully")

        except Exception as e:
            # Log the error but don't expose details to the user
            logger.exception(
                "Failed to send password reset email",
                extra={
                    "recipient": user.email,
                    "exception": str(e),
                },
            )

        # Always return the same message (don't reveal if user exists)
        return Response({
            "message": "If an account with this email exists, a password reset link has been sent."
        })
class ResetPasswordView(APIView):

    def post(self, request, uidb64, token):

        serializer = ResetPasswordSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        try:
            user_id = urlsafe_base64_decode(
                uidb64
            ).decode()

            user = User.objects.get(
                pk=user_id
            )

        except Exception:

            return Response(
                {"error": "Invalid link"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not email_verification_token.check_token(
            user,
            token
        ):

            return Response(
                {"error": "Invalid or expired token"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(
            serializer.validated_data["password"]
        )

        user.save()

        return Response({
            "message": "Password reset successful"
        })
    
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = ChangePasswordSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        user = request.user

        old_password = serializer.validated_data["old_password"]
        new_password = serializer.validated_data["new_password"]

        if not user.check_password(old_password):
            return Response(
                {
                    "error": "Old password is incorrect"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()

        return Response(
            {
                "message": "Password changed successfully"
            },
            status=status.HTTP_200_OK
        )


class ProfileStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        total_quizzes_created = Quiz.objects.filter(
            creator=request.user
        ).count()

        participations = QuizAttempt.objects.filter(
            user=request.user
        ).count()

        completed_quizzes = QuizAttempt.objects.filter(
            user=request.user,
            completed=True
        ).count()

        attempts = QuizAttempt.objects.filter(user=request.user)

        if attempts.exists():
            total_score = sum(attempt.score for attempt in attempts)
            average_score = round(total_score / attempts.count(), 2)
        else:
            average_score = 0

        return Response({
            "total_quizzes_created": total_quizzes_created,
            "participations": participations,
            "completed_quizzes": completed_quizzes,
            "average_score": average_score,
        })