from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Send a test verification email using Resend. Usage: python manage.py test_email <your_email>"

    def add_arguments(self, parser):
        parser.add_argument("email", type=str, help="Recipient email address")

    def handle(self, *args, **options):
        recipient = options["email"]

        from quizzes.email_service import send_verification_email

        # For a test email we can send a placeholder link.
        # The verification endpoint remains unchanged and will only activate a real token link.
        verification_link = "http://127.0.0.1:8000/api/auth/verify-email/test_uid/test_token/"

        try:
            send_verification_email(
                user_email=recipient,
                username="Test User",
                verification_link=verification_link,
            )
        except Exception as exc:
            self.stderr.write(f"Failed to send test email: {exc}")
            raise

        self.stdout.write(f"Test email sent successfully to {recipient}")

