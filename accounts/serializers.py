import logging

from rest_framework import serializers
from .models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed
from rest_framework import status
from django.contrib.auth.password_validation import validate_password

logger = logging.getLogger(__name__)

class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        min_length=8
    )

    class Meta:
        model = User

        fields = [
            "username",
            "email",
            "password"
        ]

    def create(self, validated_data):

        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"]
        )

        return user
    
class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):

    username_field = "email"

    def validate(self, attrs):

        email = attrs.get("email")
        password = attrs.get("password")

        user = authenticate(
            email=email,
            password=password
        )

        if user is None:
            logger.warning(
                "Login failed: invalid credentials",
                extra={"email": email}
            )
            raise AuthenticationFailed(
                {
                    "code": "INVALID_CREDENTIALS",
                    "message": "Invalid email or password."
                }
            )

        if not user.is_verified:
            logger.warning(
                "Login failed: email not verified",
                extra={"email": email, "user_id": user.id}
            )
            exc = AuthenticationFailed(
                {
                    "code": "EMAIL_NOT_VERIFIED",
                    "message": "Your email address has not been verified. Please check your inbox and click the verification link before logging in.",
                    "can_resend_verification": True
                }
            )
            exc.status_code = status.HTTP_403_FORBIDDEN
            raise exc

        logger.info(
            "Login successful",
            extra={"email": email, "user_id": user.id}
        )

        refresh = self.get_token(user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token)
        }



class ForgotPasswordSerializer(serializers.Serializer):

    email = serializers.EmailField()

class ResetPasswordSerializer(serializers.Serializer):

    password = serializers.CharField(
        min_length=8
    )

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value


class ProfileStatsSerializer(serializers.Serializer):
    total_quizzes_created = serializers.IntegerField()
    participations = serializers.IntegerField()
    completed_quizzes = serializers.IntegerField()
    average_score = serializers.FloatField()