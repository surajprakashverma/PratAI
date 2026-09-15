import truststore
truststore.inject_into_ssl()

"""
Vercel Serverless Function Entrypoint
----------------------------------------
Triggered weekly by vercel.json's cron schedule (Wednesdays).
Runs the full pipeline: fetch -> curate -> review/retry -> compose -> send.
No human approval step - the Reviewer Agent's threshold is the only gate.
"""
import sys
import os
import json

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "lib"))

from http.server import BaseHTTPRequestHandler

from pipeline import generate_verified_newsletter
from composer import compose_newsletter_html
from sender import send_newsletter


def run_newsletter_job():
    result = generate_verified_newsletter()
    newsletter = result["newsletter"]

    if newsletter is None:
        return {
            "success": True,
            "skipped": True,
            "reason": "Reviewer threshold was not met after max retries; FALLBACK_POLICY=skip, so nothing was sent this week.",
            "attempts": result["attempts"],
        }

    html = compose_newsletter_html(newsletter)

    newsletter_name = os.getenv("NEWSLETTER_NAME", "PratAI")
    subject = f"{newsletter_name} - This Week in AI"

    send_result = send_newsletter(html, subject=subject)

    return {
        "success": send_result.get("success", False),
        "skipped": False,
        "met_threshold": result["met_threshold"],
        "attempts": result["attempts"],
        "story_count": len(newsletter.get("stories", [])),
        "send_result": send_result,
    }


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            result = run_newsletter_job()
            status_code = 200 if result.get("success") else 500
        except Exception as e:
            result = {"success": False, "error": str(e)}
            status_code = 500

        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(result, indent=2).encode("utf-8"))


if __name__ == "__main__":
    # Local test - run: python api/send_newsletter.py
    result = run_newsletter_job()
    print(json.dumps(result, indent=2))