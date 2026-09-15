"""
Curator/Summarizer Agent
--------------------------
Takes raw RSS items and asks Gemini to select the best stories and
draft a complete newsletter issue (HTML-free, plain structured text
that the composer will later wrap in HTML).
"""
import json
import re
import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GOOGLE_MODEL = os.getenv("GOOGLE_Model", "gemini-2.5-flash")

llm = ChatGoogleGenerativeAI(
    model=GOOGLE_MODEL,
    google_api_key=GEMINI_API_KEY,
    temperature=0.5,
)

CURATOR_PROMPT = ChatPromptTemplate.from_template(
    """You are the editor of "{newsletter_name}", a weekly AI news digest.
Today's actual date is {current_date}. Do not assume any date is "future" or
implausible - the news items below are genuinely from around this date.

Below is a list of recent AI news items pulled from RSS feeds. Select AT LEAST
7 (seven) and up to 10 significant, interesting, and diverse stories. CRITICAL
RULE: if two or more items describe the same underlying event, announcement,
or debate (even from different sources or angles), you MUST merge them into a
SINGLE story rather than listing them separately - but when merging, pick the
SINGLE most authoritative source for the "source" field (do not combine
multiple source names with slashes).

Raw items:
---
{items_json}
---

{revision_feedback_section}

For each selected story, write:
- headline: a punchy, clear headline (not the raw RSS title, rewritten to be engaging)
- summary: 4-6 sentences (a full paragraph) explaining what happened, the key
  details/numbers/quotes involved, why it matters for the AI industry, and any
  likely implications going forward. Write in plain, authentic language (not
  corporate/marketing tone) - this should read like a knowledgeable friend
  explaining the story in depth, not a one-line blurb.
- source: exactly ONE original source name (never combine multiple sources
  with slashes or "and")
- link: the original article URL

Also write:
- intro: a 2-3 sentence friendly intro paragraph for this week's issue

Respond ONLY with valid JSON in this exact format, no other text:
{{
  "intro": "...",
  "stories": [
    {{"headline": "...", "summary": "...", "source": "...", "link": "..."}}
  ]
}}
"""
)


def _extract_text(content) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and "text" in block:
                parts.append(block["text"])
        return "".join(parts).strip()
    return str(content).strip()


def curate_newsletter(raw_items: list, newsletter_name: str = "Pratai", revision_feedback: str = "") -> dict:
    """
    Returns a dict: {intro, tldr, stories}
    (tldr is derived programmatically from story headlines, not generated
    by the LLM, to guarantee it always matches the story count exactly.)
    """
    items_json = json.dumps(raw_items, indent=2)[:12000]  # cap size to stay within context limits

    if revision_feedback:
        revision_section = (
            f"IMPORTANT - This is a REVISION. The previous draft had these issues:\n"
            f"{revision_feedback}\n"
            f"Fix these specific issues in this new version."
        )
    else:
        revision_section = ""

    chain = CURATOR_PROMPT | llm
    response = chain.invoke({
        "newsletter_name": newsletter_name,
        "items_json": items_json,
        "revision_feedback_section": revision_section,
        "current_date": datetime.now().strftime("%B %d, %Y"),
    })

    raw_text = _extract_text(response.content)
    cleaned = re.sub(r"^```(?:json)?|```$", "", raw_text.strip(), flags=re.MULTILINE).strip()

    result = json.loads(cleaned)
    result["tldr"] = [s["headline"] for s in result.get("stories", [])]
    return result


if __name__ == "__main__":
    from rss_fetcher import fetch_recent_items

    items = fetch_recent_items()
    print(f"Fetched {len(items)} raw items. Curating...\n")

    result = curate_newsletter(items)
    print(json.dumps(result, indent=2))