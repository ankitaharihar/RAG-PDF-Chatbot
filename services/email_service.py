import os
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv

load_dotenv()

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "").strip()
APP_URL = os.getenv("APP_URL", "http://localhost:8501").rstrip("/")


def send_password_reset_email(to_email: str, token: str) -> tuple[bool, str]:
    if not RESEND_API_KEY:
        return False, "RESEND_API_KEY is missing."

    query = urlencode({
        "mode": "reset",
        "email": to_email,
        "token": token,
    })

    reset_url = f"{APP_URL}/?{query}"

    response = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "from": "StudyAI <onboarding@resend.dev>",
            "to": [to_email],
            "subject": "Reset your StudyAI password",
            "html": f"""
                <div style="font-family:Arial,sans-serif;max-width:520px;margin:auto;">
                    <h2>Reset your password</h2>

                    <p>
                        We received a request to reset your StudyAI password.
                    </p>

                    <p>
                        <a
                            href="{reset_url}"
                            style="
                                display:inline-block;
                                padding:12px 20px;
                                background:#2563eb;
                                color:white;
                                text-decoration:none;
                                border-radius:8px;
                                font-weight:bold;
                            "
                        >
                            Reset Password
                        </a>
                    </p>

                    <p>
                        This link expires in 20 minutes and can only be used once.
                    </p>

                    <p>
                        If you didn't request this password reset,
                        you can ignore this email.
                    </p>
                </div>
            """,
        },
        timeout=15,
    )

    if response.status_code in (200, 201):
        return True, "Password reset email sent."

    return False, f"Email service error: {response.text}"