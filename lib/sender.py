import truststore
truststore.inject_into_ssl()

"""
Email Sender (via Resend HTTPS API)
--------------------------------------
Sends the composed newsletter HTML to the configured recipient list.
"""
import os
import requests
from dotenv import load_dotenv
load_dotenv()

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
RECIPIENT_EMAILS = os.getenv("RECIPIENT_EMAILS", "")
NEWSLETTER_NAME = os.getenv("NEWSLETTER_NAME", "PratAI")

RESEND_API_URL = "https://api.resend.com/emails"


def get_recipient_list() -> list:
    return [email.strip() for email in RECIPIENT_EMAILS.split(",") if email.strip()]


def debug_recipient_value() -> dict:
    return {
        "raw_value": repr(RECIPIENT_EMAILS),
        "parsed_list": get_recipient_list(),
        "api_key_prefix": RESEND_API_KEY[:6] if RESEND_API_KEY else "(empty)",
        "api_key_length": len(RESEND_API_KEY),
    }


def send_newsletter(html_body: str, subject: str = None) -> dict:
    recipients = get_recipient_list()

    if not recipients:
        return {"success": False, "error": "No recipients configured in RECIPIENT_EMAILS."}

    if subject is None:
        subject = f"{NEWSLETTER_NAME} - This Week in AI"

    response = requests.post(
        RESEND_API_URL,
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "from": "onboarding@resend.dev",
            "to": recipients,
            "subject": subject,
            "html": html_body,
        },
        timeout=20,
    )

    if response.status_code >= 400:
        return {"success": False, "error": f"{response.status_code}: {response.text}"}

    return {"success": True, "recipients": recipients, "response": response.json()}


if __name__ == "__main__":
    test_html = "<html><body><h1>PratAI Test</h1><p>This is a test send.</p></body></html>"
    result = send_newsletter(test_html, subject="Pratai - Test Email")
    print(result)
