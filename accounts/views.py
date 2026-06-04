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
from .serializers import ChangePasswordSerializer


class RegisterView(generics.CreateAPIView):

    queryset = User.objects.all()
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        uidb64 = urlsafe_base64_encode(
            force_bytes(user.id)
        )

        token = email_verification_token.make_token(user)

        verification_link = (
            f"http://127.0.0.1:8000/api/auth/verify-email/"
            f"{uidb64}/{token}/"
        )

        return Response({
            "message": "User registered successfully",
            "verification_link": verification_link
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

        try:
            user_id = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=user_id)

        except Exception:
            return Response(
                {"error": "Invalid verification link"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if email_verification_token.check_token(user, token):

            user.is_verified = True
            user.save()

            return Response({
                "message": "Email verified successfully"
            })

        return Response(
            {"error": "Invalid or expired token"},
            status=status.HTTP_400_BAD_REQUEST
        )
class ForgotPasswordView(APIView):

    def post(self, request):

        serializer = ForgotPasswordSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)

        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=404
            )

        uidb64 = urlsafe_base64_encode(
            force_bytes(user.id)
        )

        token = email_verification_token.make_token(
            user
        )

        reset_link = (
            f"http://127.0.0.1:8000/api/auth/reset-password/"
            f"{uidb64}/{token}/"
        )

        return Response({
            "message": "Password reset link generated",
            "reset_link": reset_link
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