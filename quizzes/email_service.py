import logging
from typing import Optional

from django.conf import settings

# Resend SDK
import resend  # noqa: F401

logger = logging.getLogger(__name__)


def send_verification_email(
    user_email: str,
    username: str,
    verification_link: str,
    *,
    html_override: Optional[str] = None,
):
    """Send verification email via Resend.

    Never raises to the registration endpoint callers; they can decide how to handle failures.
    """
    if not getattr(settings, "RESEND_API_KEY", None):
        raise RuntimeError("RESEND_API_KEY is not configured")

    if resend is None:  # pragma: no cover
        raise RuntimeError("Resend SDK is not installed or could not be imported")

    sender = getattr(settings, "EMAIL_FROM", "LetsQuiz <noreply@letsquiz.online>")

    subject = "Verify Your LetsQuiz Account"

    html = html_override or f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Verify Your LetsQuiz Account</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; line-height: 1.5; color: #111827; background-color: #f9fafb;">
        <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <tr>
                <td style="background-color: #ffffff; border-radius: 8px; padding: 32px;">
                    <!-- Header -->
                    <h1 style="margin: 0 0 24px 0; font-size: 24px; font-weight: 600; color: #111827; text-align: center;">
                        LetsQuiz
                    </h1>

                    <!-- Title -->
                    <h2 style="margin: 0 0 16px 0; font-size: 20px; font-weight: 600; color: #111827;">
                        Verify Your LetsQuiz Account
                    </h2>

                    <!-- Body -->
                    <p style="margin: 0 0 16px 0; font-size: 16px; color: #374151;">
                        Welcome to LetsQuiz!
                    </p>
                    <p style="margin: 0 0 24px 0; font-size: 16px; color: #374151;">
                        Thanks for creating your account. Please click the button below to verify your email.
                    </p>

                    <!-- Button -->
                    <table width="100%" cellpadding="0" cellspacing="0">
                        <tr>
                            <td align="center" style="padding: 24px 0;">
                                <a href="{verification_link}"
                                   style="display: inline-block; padding: 14px 28px; background: #2563eb; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                                    Verify Email
                                </a>
                            </td>
                        </tr>
                    </table>

                    <!-- Plain text link -->
                    <p style="margin: 0 0 12px 0; font-size: 14px; color: #6b7280;">
                        If the button doesn't work, copy and paste this link into your browser:
                    </p>
                    <p style="margin: 0; word-break: break-all; font-size: 14px;">
                        <a href="{verification_link}" style="color: #2563eb;">{verification_link}</a>
                    </p>
                </td>
            </tr>

            <!-- Footer -->
            <tr>
                <td style="padding: 24px 0; text-align: center;">
                    <p style="margin: 0 0 4px 0; font-size: 14px; color: #6b7280;">
                        &copy; LetsQuiz
                    </p>
                    <p style="margin: 0; font-size: 12px; color: #9ca3af;">
                        Create. Challenge. Learn.
                    </p>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    try:
        # Assign API key and send email
        resend.api_key = settings.RESEND_API_KEY

        logger.info(
            "Sending verification email",
            extra={
                "recipient": user_email,
                "username": username,
            }
        )

        # Resend expects a structure compatible with its SDK.
        # Using the documented pattern: resend.Emails.send({...})
        response = resend.Emails.send(
            {
                "from": sender,
                "to": [user_email],
                "subject": subject,
                "html": html,
            }
        )

        # Log success with recipient and response id
        response_id = response.get("id") if isinstance(response, dict) else str(response)
        logger.info(
            "Verification email sent successfully",
            extra={
                "recipient": user_email,
                "resend_response_id": response_id,
            }
        )

        return response
    except Exception as e:
        logger.error(
            "Failed to send verification email",
            extra={
                "recipient": user_email,
                "error": str(e),
            },
            exc_info=True
        )
        raise


def send_password_reset_email(
    user_email: str,
    username: str,
    reset_link: str,
    *,
    html_override: Optional[str] = None,
):
    """Send password reset email via Resend.

    Never raises to the forgot password endpoint callers; they can decide how to handle failures.
    """
    if not getattr(settings, "RESEND_API_KEY", None):
        raise RuntimeError("RESEND_API_KEY is not configured")

    if resend is None:  # pragma: no cover
        raise RuntimeError("Resend SDK is not installed or could not be imported")

    sender = getattr(settings, "EMAIL_FROM", "LetsQuiz <noreply@letsquiz.online>")

    subject = "Reset Your LetsQuiz Password"

    html = html_override or f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Reset Your Password</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; line-height: 1.5; color: #111827; background-color: #f9fafb;">
        <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <tr>
                <td style="background-color: #ffffff; border-radius: 8px; padding: 32px;">
                    <!-- Header -->
                    <h1 style="margin: 0 0 24px 0; font-size: 24px; font-weight: 600; color: #111827; text-align: center;">
                        LetsQuiz
                    </h1>

                    <!-- Title -->
                    <h2 style="margin: 0 0 16px 0; font-size: 20px; font-weight: 600; color: #111827;">
                        Reset Your Password
                    </h2>

                    <!-- Body -->
                    <p style="margin: 0 0 16px 0; font-size: 16px; color: #374151;">
                        Hi {username},
                    </p>
                    <p style="margin: 0 0 24px 0; font-size: 16px; color: #374151;">
                        We received a request to reset your password. Click the button below to create a new password.
                    </p>

                    <!-- Button -->
                    <table width="100%" cellpadding="0" cellspacing="0">
                        <tr>
                            <td align="center" style="padding: 24px 0;">
                                <a href="{reset_link}"
                                   style="display: inline-block; padding: 14px 28px; background: #2563eb; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                                    Reset Password
                                </a>
                            </td>
                        </tr>
                    </table>

                    <!-- Plain text link -->
                    <p style="margin: 0 0 12px 0; font-size: 14px; color: #6b7280;">
                        If the button doesn't work, copy and paste this link into your browser:
                    </p>
                    <p style="margin: 0; word-break: break-all; font-size: 14px;">
                        <a href="{reset_link}" style="color: #2563eb;">{reset_link}</a>
                    </p>

                    <!-- Security notice -->
                    <p style="margin: 24px 0 12px 0; font-size: 14px; color: #6b7280;">
                        If you didn't request a password reset, you can safely ignore this email.
                    </p>
                </td>
            </tr>

            <!-- Footer -->
            <tr>
                <td style="padding: 24px 0; text-align: center;">
                    <p style="margin: 0 0 4px 0; font-size: 14px; color: #6b7280;">
                        &copy; LetsQuiz
                    </p>
                    <p style="margin: 0; font-size: 12px; color: #9ca3af;">
                        Create. Challenge. Learn.
                    </p>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    try:
        # Assign API key and send email
        resend.api_key = settings.RESEND_API_KEY

        logger.info(
            "Sending password reset email",
            extra={
                "recipient": user_email,
                "username": username,
            }
        )

        # Resend expects a structure compatible with its SDK.
        # Using the documented pattern: resend.Emails.send({...})
        response = resend.Emails.send(
            {
                "from": sender,
                "to": [user_email],
                "subject": subject,
                "html": html,
            }
        )

        # Log success with recipient and response id
        response_id = response.get("id") if isinstance(response, dict) else str(response)
        logger.info(
            "Password reset email sent successfully",
            extra={
                "recipient": user_email,
                "resend_response_id": response_id,
            }
        )

        return response
    except Exception as e:
        logger.error(
            "Failed to send password reset email",
            extra={
                "recipient": user_email,
                "error": str(e),
            },
            exc_info=True
        )
        raise