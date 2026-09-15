"""
Pipeline Orchestrator
----------------------
Ties Curator -> Reviewer together with a scored retry loop.
Since Pratai has no human approval step, this retry loop is the only
quality gate before sending - it must run to a sensible conclusion.
"""
import os
from dotenv import load_dotenv
load_dotenv()

from rss_fetcher import fetch_recent_items
from curator import curate_newsletter
from reviewer import review_newsletter

MAX_RETRIES = int(os.getenv("MAX_RETRIES", "5"))
SCORE_THRESHOLD = int(os.getenv("SCORE_THRESHOLD", "7"))
NEWSLETTER_NAME = os.getenv("NEWSLETTER_NAME", "Pratai")

# If nothing clears SCORE_THRESHOLD after MAX_RETRIES attempts:
#   "send_best"  -> send the best-scoring draft anyway (current/original behavior)
#   "skip"       -> do not send anything that week (safer for fully unattended runs)
FALLBACK_POLICY = os.getenv("FALLBACK_POLICY", "send_best")


def _build_feedback_text(review_result: dict) -> str:
    parts = []

    rule_result = review_result.get("rule_result") or {}
    if rule_result.get("issues"):
        parts.append("Rule-based issues: " + "; ".join(rule_result["issues"]))

    critic_result = review_result.get("critic_result") or {}
    if critic_result.get("feedback"):
        parts.append(f"Editor feedback (score {critic_result.get('score', '?')}/10): {critic_result['feedback']}")

    return "\n".join(parts) if parts else "General quality issue - please improve clarity and diversity of topics."


def generate_verified_newsletter() -> dict:
    """
    Runs the full fetch -> curate -> review -> retry loop.

    Returns:
      {
        "newsletter": <best newsletter dict, or None if FALLBACK_POLICY is "skip" and threshold was never met>,
        "attempts": <int>,
        "final_review": <review result dict>,
        "met_threshold": <bool>,
        "skipped": <bool>,
      }
    """
    print("Fetching raw news items...")
    raw_items = fetch_recent_items()
    print(f"Fetched {len(raw_items)} items.\n")

    best_newsletter = None
    best_score = -1
    best_review = None
    revision_feedback = ""

    for attempt in range(1, MAX_RETRIES + 1):
        print(f"--- Attempt {attempt}/{MAX_RETRIES} ---")

        newsletter = curate_newsletter(raw_items, newsletter_name=NEWSLETTER_NAME, revision_feedback=revision_feedback)
        review = review_newsletter(newsletter, newsletter_name=NEWSLETTER_NAME)

        critic_score = (review.get("critic_result") or {}).get("score", 0)
        rule_passed = (review.get("rule_result") or {}).get("passed", False)
        effective_score = critic_score if rule_passed else 0

        print(f"Rule-based passed: {rule_passed} | Critic score: {critic_score}/10 | Overall passed: {review['passed']}")
        if not review["passed"]:
            feedback = (review.get("critic_result") or {}).get("feedback", "")
            if feedback:
                print(f"  Feedback: {feedback}")
            if rule_result_issues := (review.get("rule_result") or {}).get("issues"):
                print(f"  Rule issues: {rule_result_issues}")

        if effective_score > best_score:
            best_score = effective_score
            best_newsletter = newsletter
            best_review = review

        if review["passed"] and critic_score >= SCORE_THRESHOLD:
            print(f"Threshold met on attempt {attempt} (score {critic_score}/10). Stopping loop.\n")
            return {
                "newsletter": newsletter,
                "attempts": attempt,
                "final_review": review,
                "met_threshold": True,
                "skipped": False,
            }

        revision_feedback = _build_feedback_text(review)

    if FALLBACK_POLICY == "skip":
        print(f"Max retries reached. Best score was {best_score}/10 (below threshold {SCORE_THRESHOLD}). "
              f"FALLBACK_POLICY=skip -> not sending this week.\n")
        return {
            "newsletter": None,
            "attempts": MAX_RETRIES,
            "final_review": best_review,
            "met_threshold": False,
            "skipped": True,
        }

    print(f"Max retries reached. FALLBACK_POLICY=send_best -> using best draft seen (score {best_score}/10).\n")
    return {
        "newsletter": best_newsletter,
        "attempts": MAX_RETRIES,
        "final_review": best_review,
        "met_threshold": False,
        "skipped": False,
    }


if __name__ == "__main__":
    import json
    result = generate_verified_newsletter()
    print("FINAL RESULT")
    print("=" * 60)
    print(f"Met threshold: {result['met_threshold']} | Attempts: {result['attempts']} | Skipped: {result['skipped']}")
    print("=" * 60)
    if result["newsletter"]:
        print(json.dumps(result["newsletter"], indent=2))
    else:
        print("No newsletter was generated (skipped).")