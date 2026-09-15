"""
Reviewer Agent
--------------
Two-layer QA gate for the newsletter draft, since there is no human
approval step for Pratai:

  Layer 1 (rule-based, fast, free):
    - minimum number of stories
    - each story has a headline, summary, source, and link
    - no leaked API keys/secrets/tokens
    - no leftover placeholder/template text
    - reasonable summary length (not empty, not absurdly long)

  Layer 2 (LLM critic, uses Gemini):
    - checks editorial quality, diversity of topics, clarity, depth,
      and source cleanliness
    - returns PASS/FAIL + specific feedback for revision
"""
import os
import re
import json
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GOOGLE_MODEL = os.getenv("GOOGLE_Model", "gemini-2.5-flash")

critic_llm = ChatGoogleGenerativeAI(
    model=GOOGLE_MODEL,
    google_api_key=GEMINI_API_KEY,
    temperature=0.2,
)

SECRET_PATTERNS = [
    r"AIza[0-9A-Za-z\-_]{35}",
    r"sk-[A-Za-z0-9]{20,}",
    r"re_[A-Za-z0-9]{20,}",
    r"(?i)api[_-]?key\s*[:=]\s*\S+",
    r"(?i)secret[_-]?key\s*[:=]\s*\S+",
    r"Bearer\s+[A-Za-z0-9\-_.]+",
]

PLACEHOLDER_PATTERNS = [
    r"\bTODO\b", r"\bXXXX\b", r"\blorem ipsum\b", r"\{\{.*?\}\}",
]

MIN_STORIES = 7
MAX_STORIES = 10
MIN_SUMMARY_LEN = 200
MAX_SUMMARY_LEN = 1200


def rule_based_check(newsletter: dict) -> dict:
    issues = []

    stories = newsletter.get("stories", [])
    if len(stories) < MIN_STORIES:
        issues.append(f"Too few stories: {len(stories)} (min {MIN_STORIES})")
    if len(stories) > MAX_STORIES:
        issues.append(f"Too many stories: {len(stories)} (max {MAX_STORIES})")

    if not newsletter.get("intro", "").strip():
        issues.append("Missing intro paragraph")

    if not newsletter.get("tldr") or len(newsletter.get("tldr", [])) < 2:
        issues.append("TL;DR section missing or too short")

    for i, story in enumerate(stories):
        headline = story.get("headline", "").strip()
        summary = story.get("summary", "").strip()
        source = story.get("source", "").strip()
        link = story.get("link", "").strip()

        if not headline:
            issues.append(f"Story {i+1}: missing headline")
        if not source:
            issues.append(f"Story {i+1}: missing source")
        if "/" in source or " and " in source.lower():
            issues.append(f"Story {i+1}: source field contains multiple outlets ('{source}') - must be a single source")
        if not link or not link.startswith("http"):
            issues.append(f"Story {i+1}: missing or invalid link")
        if len(summary) < MIN_SUMMARY_LEN:
            issues.append(f"Story {i+1}: summary too short ({len(summary)} chars, need at least {MIN_SUMMARY_LEN})")
        if len(summary) > MAX_SUMMARY_LEN:
            issues.append(f"Story {i+1}: summary too long ({len(summary)} chars)")

    full_text = json.dumps(newsletter)
    for pattern in SECRET_PATTERNS:
        if re.search(pattern, full_text):
            issues.append(f"Potential leaked secret detected (pattern: {pattern})")

    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, full_text, re.IGNORECASE):
            issues.append(f"Leftover placeholder text detected (pattern: {pattern})")

    return {
        "passed": len(issues) == 0,
        "issues": issues,
        "story_count": len(stories),
    }


CRITIC_PROMPT = ChatPromptTemplate.from_template(
    """You are a strict editor reviewing a draft weekly AI newsletter called "{newsletter_name}"
before it gets sent out automatically, with no human review.
Today's actual date is {current_date}. Do not flag dates around this time as
"future-dated" or assume news mentioning this date is hallucinated - it is genuinely current.

Draft newsletter (JSON):
---
{newsletter_json}
---

Evaluate the draft on:
1. Editorial quality - are the summaries clear, accurate-sounding, and well-written (not robotic or repetitive)?
2. Topic diversity - do the stories cover meaningfully different topics, not 3+ stories about the exact same announcement?
3. Relevance - are these genuinely significant AI stories, not trivial or off-topic items?
4. Tone - professional but engaging, appropriate for a subscriber's inbox.
5. Depth - is each summary a genuine multi-sentence paragraph (4-6 sentences) with
   real substance and detail, not a shallow one-liner? Fail the draft if most
   summaries feel thin or underdeveloped.
6. Source cleanliness - does each story have exactly ONE clean source name
   (not multiple sources combined with slashes)? Fail if any "source" field
   contains multiple outlet names joined together.

Respond ONLY with valid JSON in this exact format, no other text:
{{
  "passed": true or false,
  "score": 1-10,
  "feedback": "specific, actionable feedback if passed is false, otherwise empty string"
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


def llm_critic_check(newsletter: dict, newsletter_name: str = "Pratai") -> dict:
    chain = CRITIC_PROMPT | critic_llm
    response = chain.invoke({
        "newsletter_name": newsletter_name,
        "newsletter_json": json.dumps(newsletter, indent=2),
        "current_date": datetime.now().strftime("%B %d, %Y"),
    })
    raw_text = _extract_text(response.content)
    cleaned = re.sub(r"^```(?:json)?|```$", "", raw_text.strip(), flags=re.MULTILINE).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "passed": False,
            "score": 0,
            "feedback": f"Critic response was not valid JSON: {raw_text[:200]}",
        }


def review_newsletter(newsletter: dict, newsletter_name: str = "Pratai") -> dict:
    rule_result = rule_based_check(newsletter)

    if not rule_result["passed"]:
        return {
            "passed": False,
            "layer_failed": "rule_based",
            "rule_result": rule_result,
            "critic_result": None,
        }

    critic_result = llm_critic_check(newsletter, newsletter_name)

    return {
        "passed": rule_result["passed"] and critic_result.get("passed", False),
        "layer_failed": None if critic_result.get("passed", False) else "llm_critic",
        "rule_result": rule_result,
        "critic_result": critic_result,
    }


if __name__ == "__main__":
    from rss_fetcher import fetch_recent_items
    from curator import curate_newsletter

    items = fetch_recent_items()
    newsletter = curate_newsletter(items)

    print("Reviewing newsletter draft...\n")
    result = review_newsletter(newsletter)
    print(json.dumps(result, indent=2))