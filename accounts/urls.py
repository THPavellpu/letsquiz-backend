from django.urls import path

from .views import (
    ChangePasswordView,
    RegisterView,
    ProfileView,
    EmailLoginView,
    VerifyEmailView,
    ForgotPasswordView,
    ResetPasswordView,
    ProfileStatsView,
    ResendVerificationView,

)

from rest_framework_simplejwt.views import (
    TokenRefreshView,
)
urlpatterns = [

    path(
        "register/",
        RegisterView.as_view(),
        name="register"
    ),
    path(
        "login/",
        EmailLoginView.as_view(),
        name="login"
    ),

    path(
        "refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh"
    ),
    path(
    "profile/",
    ProfileView.as_view(),
    name="profile"
    ),
    path(
    "verify-email/<uidb64>/<token>/",
    VerifyEmailView.as_view(),
    name="verify-email"
    ),
    path(
    "forgot-password/",
    ForgotPasswordView.as_view(),
    name="forgot-password"
    ),
    path(
    "reset-password/<uidb64>/<token>/",
    ResetPasswordView.as_view(),
    name="reset-password"),
    path(
    "change-password/",
    ChangePasswordView.as_view(),
    name="change-password"
    ),
    path(
    "profile-stats/",
    ProfileStatsView.as_view(),
    name="profile-stats"
    ),
    path(
        "resend-verification/",
        ResendVerificationView.as_view(),
        name="resend-verification"
    ),
]
