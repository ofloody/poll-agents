"""Email verification service."""

import secrets
import string
from email.message import EmailMessage

import aiosmtplib

from .config.settings import SMTPSettings


class EmailService:
    """Service for sending verification emails."""

    def __init__(self, settings: SMTPSettings):
        self.settings = settings

    def generate_verification_code(self, length: int = 6) -> str:
        """Generate a random numeric verification code."""
        return "".join(secrets.choice(string.digits) for _ in range(length))

    async def send_verification_email(self, to_email: str, code: str) -> bool:
        """Send verification code via SMTP.

        Returns True if email sent successfully, False otherwise.
        """
        message = EmailMessage()
        message["From"] = self.settings.sender_email
        message["To"] = to_email
        message["Subject"] = "Poll Agents - Verification Code"
        message.set_content(f"""\
Welcome to Poll Agents!

Your verification code is: {code}

This code will expire in 5 minutes.

Thank you for participating.
""")

        try:
            await aiosmtplib.send(
                message,
                hostname=self.settings.host,
                port=self.settings.port,
                username=self.settings.username,
                password=self.settings.password,
                start_tls=self.settings.use_tls,
            )
            print(f"[EMAIL] Verification code sent to {to_email}")
            return True
        except Exception as e:
            print(f"[EMAIL ERROR] Failed to send to {to_email}: {e}")
            return False
