"""
Email Composer
---------------
Converts the curated newsletter JSON into a styled HTML email,
including the CAN-SPAM required physical address in the footer.
"""
import os
from dotenv import load_dotenv
load_dotenv()

NEWSLETTER_NAME = os.getenv("NEWSLETTER_NAME", "PratAI")
PHYSICAL_ADDRESS = os.getenv("PHYSICAL_ADDRESS", "")

_LT = chr(60)
_GT = chr(62)
_Q = chr(34)


def _story_block(story: dict) -> str:
    headline = story.get("headline", "")
    summary = story.get("summary", "")
    source = story.get("source", "")
    link = story.get("link", "")

    source_link = (
        _LT + "a href=" + _Q + link + _Q + " style=" + _Q
        + "color:#0A66C2;text-decoration:none;font-weight:600;" + _Q + _GT
        + source + _LT + "/a" + _GT
    )

    return (
        "<div style=" + _Q + "margin-bottom:22px;padding-bottom:20px;border-bottom:1px solid #eef0f4;" + _Q + ">"
        + "<h3 style=" + _Q + "font-size:17px;margin:0 0 8px 0;color:#1a1a2e;" + _Q + ">"
        + _LT + "a href=" + _Q + link + _Q + " style=" + _Q + "color:#1a1a2e;text-decoration:none;" + _Q + _GT
        + headline + _LT + "/a" + _GT
        + "</h3>"
        + "<p style=" + _Q + "font-size:14px;line-height:1.6;color:#3a3f4b;margin:0 0 6px 0;" + _Q + ">"
        + summary + "</p>"
        + "<p style=" + _Q + "font-size:12px;color:#8a8f9a;margin:0;" + _Q + ">Source: " + source_link + "</p>"
        + "</div>"
    )


def compose_newsletter_html(newsletter: dict) -> str:
    intro = newsletter.get("intro", "")
    tldr = newsletter.get("tldr", [])
    stories = newsletter.get("stories", [])

    tldr_items = "".join(
        "<li style=" + _Q + "margin-bottom:6px;font-size:14px;color:#3a3f4b;" + _Q + ">" + item + "</li>"
        for item in tldr
    )

    story_blocks = "".join(_story_block(s) for s in stories)

    html = (
        "<!DOCTYPE html><html><body style=" + _Q
        + "font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Arial,sans-serif;"
        "background:#f4f6fb;margin:0;padding:30px 16px;" + _Q + ">"
        + "<div style=" + _Q + "max-width:600px;margin:0 auto;background:#ffffff;border-radius:14px;"
        "overflow:hidden;box-shadow:0 10px 30px rgba(20,40,80,0.08);" + _Q + ">"

        + "<div style=" + _Q + "background:linear-gradient(135deg,#1a1a2e,#0A66C2);padding:28px 30px;" + _Q + ">"
        + "<h1 style=" + _Q + "color:#ffffff;margin:0;font-size:24px;" + _Q + ">" + NEWSLETTER_NAME + "</h1>"
        + "<p style=" + _Q + "color:#cdd8ef;margin:6px 0 0 0;font-size:13px;" + _Q + ">Your weekly AI news digest</p>"
        + "</div>"

        + "<div style=" + _Q + "padding:28px 30px;" + _Q + ">"
        + "<p style=" + _Q + "font-size:15px;line-height:1.6;color:#1a1a2e;margin:0 0 22px 0;" + _Q + ">" + intro + "</p>"

        + "<div style=" + _Q + "background:#f7f9fc;border-radius:10px;padding:16px 20px;margin-bottom:26px;" + _Q + ">"
        + "<p style=" + _Q + "font-weight:600;font-size:13px;color:#0A66C2;margin:0 0 8px 0;"
          "text-transform:uppercase;letter-spacing:0.5px;" + _Q + ">This Week's Highlights</p>"
        + "<ul style=" + _Q + "margin:0;padding-left:18px;" + _Q + ">" + tldr_items + "</ul>"
        + "</div>"

        + story_blocks

        + "</div>"

        + "<div style=" + _Q + "background:#f7f9fc;padding:22px 30px;text-align:center;" + _Q + ">"
        + "<p style=" + _Q + "font-size:12px;color:#8a8f9a;margin:0 0 6px 0;" + _Q + ">"
        + NEWSLETTER_NAME + " | " + PHYSICAL_ADDRESS + "</p>"
        + "<p style=" + _Q + "font-size:11px;color:#b0b4bd;margin:0;" + _Q + ">"
        + "You are receiving this email as a subscriber to " + NEWSLETTER_NAME + "."
        + "</p>"
        + "</div>"

        + "</div></body></html>"
    )

    return html


if __name__ == "__main__":
    sample = {
        "intro": "This is a test intro.",
        "tldr": ["Point one.", "Point two."],
        "stories": [
            {"headline": "Test Headline", "summary": "Test summary text here.", "source": "Test Source", "link": "https://example.com"}
        ],
    }
    html = compose_newsletter_html(sample)
    print(html[:700])
    print(f"\nTotal length: {len(html)} characters")
