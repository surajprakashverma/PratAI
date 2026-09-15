"""
RSS Fetcher
------------
Pulls recent AI news items from a curated list of RSS feeds, covering
official AI labs, mainstream tech press, research, and specialized
AI-focused newsletters/blogs.
"""
import feedparser
from datetime import datetime, timedelta, timezone

AI_NEWS_FEEDS = [
    # Official AI labs
    "https://openai.com/news/rss.xml",
    "https://www.any-feeds.com/api/feeds/custom/cmlvzoxzq0000k004xiy14qf6/rss.xml",  # Anthropic (mirrored feed)
    "https://deepmind.google/blog/rss.xml",
    "https://huggingface.co/blog/feed.xml",

    # Google / research
    "https://research.google/blog/rss/",

    # Mainstream tech press - AI sections
    "https://www.technologyreview.com/topic/artificial-intelligence/feed",
    "https://venturebeat.com/category/ai/feed/",
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "https://arstechnica.com/ai/feed/",
    "https://www.wired.com/feed/tag/ai/latest/rss",

    # Specialized AI newsletters / blogs
    "https://importai.substack.com/feed",  # Import AI by Jack Clark (Substack)

    # Research
    "https://rss.arxiv.org/rss/cs.AI",
]


def fetch_recent_items(days_back=7, max_items_per_feed=5):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
    all_items = []

    for feed_url in AI_NEWS_FEEDS:
        try:
            parsed = feedparser.parse(feed_url)
            source_name = parsed.feed.get("title", feed_url)

            if not parsed.entries:
                status = getattr(parsed, "status", "unknown")
                bozo = getattr(parsed, "bozo", None)
                bozo_msg = getattr(parsed, "bozo_exception", "")
                print("No entries for " + feed_url + " | status=" + str(status) + " | bozo=" + str(bozo) + " | " + str(bozo_msg))

            count = 0
            for entry in parsed.entries:
                if count >= max_items_per_feed:
                    break

                published = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

                if published and published < cutoff:
                    continue

                all_items.append({
                    "title": entry.get("title", "Untitled"),
                    "link": entry.get("link", ""),
                    "summary": entry.get("summary", "")[:1500],
                    "source": source_name,
                    "published": published.isoformat() if published else "unknown",
                })
                count += 1
        except Exception as e:
            print("Failed to fetch " + feed_url + ": " + str(e))
            continue

    return all_items


if __name__ == "__main__":
    items = fetch_recent_items()
    print("\nFetched " + str(len(items)) + " items total.\n")

    by_source = {}
    for item in items:
        by_source.setdefault(item["source"], 0)
        by_source[item["source"]] += 1

    print("Items per source:")
    for source, count in by_source.items():
        print("  " + source + ": " + str(count))

    print("\nSample titles:")
    for item in items[:15]:
        print("- [" + item["source"] + "] " + item["title"])
