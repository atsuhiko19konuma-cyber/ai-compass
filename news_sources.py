from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Optional

import feedparser
import requests

from utils import clean_text


RSS_FEEDS = [
    {
        "name": "OpenAI News",
        "url": "https://openai.com/news/rss.xml",
        "credibility": 5,
        "perspective": "official",
    },
    {
        "name": "OpenAI Blog",
        "url": "https://openai.com/blog/rss.xml",
        "credibility": 5,
        "perspective": "official",
    },
    {
        "name": "Anthropic News",
        "url": "https://www.anthropic.com/news/rss",
        "credibility": 5,
        "perspective": "official",
    },
    {
        "name": "Google AI Blog",
        "url": "https://blog.google/technology/ai/rss/",
        "credibility": 5,
        "perspective": "official",
    },
    {
        "name": "Google Research Blog",
        "url": "https://research.google/blog/rss/",
        "credibility": 4,
        "perspective": "official",
    },
    {
        "name": "Google DeepMind Blog",
        "url": "https://deepmind.google/discover/blog/rss.xml",
        "credibility": 4,
        "perspective": "official",
    },
    {
        "name": "Hugging Face Blog",
        "url": "https://huggingface.co/blog/feed.xml",
        "credibility": 3,
        "perspective": "builder",
    },
    {
        "name": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "credibility": 4,
        "perspective": "media",
    },
    {
        "name": "VentureBeat AI",
        "url": "https://venturebeat.com/category/ai/feed/",
        "credibility": 4,
        "perspective": "media",
    },
    {
        "name": "The Verge",
        "url": "https://www.theverge.com/rss/index.xml",
        "credibility": 4,
        "perspective": "media",
    },
    {
        "name": "Ars Technica AI",
        "url": "https://arstechnica.com/ai/feed/",
        "credibility": 4,
        "perspective": "media",
    },
    {
        "name": "MIT Technology Review AI",
        "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed",
        "credibility": 4,
        "perspective": "media",
    },
    {
        "name": "Planet AI",
        "url": "https://planet-ai.net/rss.xml",
        "credibility": 3,
        "perspective": "curated",
    },
]


PRACTICAL_KEYWORDS = [
    "chatgpt",
    "openai",
    "claude",
    "anthropic",
    "gemini",
    "google",
    "workspace",
    "microsoft",
    "agents",
    "agent",
    "assistant",
    "productivity",
    "business",
    "enterprise",
    "automation",
    "email",
    "docs",
    "sheets",
    "slides",
    "meeting",
    "voice",
    "audio",
    "video",
    "image",
    "search",
    "coding",
    "developer",
    "tool",
    "app",
    "model",
    "api",
    "release",
    "launch",
    "hands-on",
    "guide",
    "how to",
    "review",
    "comparison",
    "strategy",
    "workflow",
    "office",
    "marketing",
    "sales",
    "customer support",
    "notebooklm",
    "perplexity",
    "cursor",
    "copilot",
    "notion",
    "canva",
    "zapier",
    "slack",
    "gmail",
    "excel",
    "spreadsheet",
]

INTEREST_KEYWORDS_PATH = Path("interest_keywords.txt")

AVOID_KEYWORDS = [
    "crypto",
    "token",
    "doom",
    "agi doom",
    "alignment paper",
    "benchmark",
    "arxiv",
    "theorem",
    "lawsuit",
    "rumor",
    "leak",
    "funding round",
    "raises $",
    "valuation",
]


def fetch_articles(days_back: int = 3) -> list[dict[str, Any]]:
    """Fetch recent articles from RSS feeds. Broken feeds are skipped quietly."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
    articles: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    for feed in RSS_FEEDS:
        try:
            response = requests.get(feed["url"], timeout=12)
            response.raise_for_status()
            parsed = feedparser.parse(response.content)
        except Exception:
            continue

        for entry in parsed.entries[:20]:
            url = entry.get("link", "")
            if not url or url in seen_urls:
                continue

            published = parse_entry_date(entry)
            if published and published < cutoff:
                continue

            title = clean_text(entry.get("title", ""))
            summary = clean_text(entry.get("summary", entry.get("description", "")))
            if not title:
                continue

            seen_urls.add(url)
            articles.append(
                {
                    "title": title,
                    "summary": summary[:900],
                    "url": url,
                    "source": feed["name"],
                    "published": published.isoformat() if published else "",
                    "credibility": feed["credibility"],
                    "perspective": feed.get("perspective", "media"),
                }
            )

    return articles


def parse_entry_date(entry: Any) -> Optional[datetime]:
    for key in ("published", "updated", "created"):
        value = entry.get(key)
        if not value:
            continue
        try:
            parsed = parsedate_to_datetime(value)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except Exception:
            continue
    return None


def select_top_articles(articles: list[dict[str, Any]], limit: int = 3) -> list[dict[str, Any]]:
    """Score locally first, then keep the final 3 diverse and practical."""
    scored_articles = []
    interest_keywords = load_interest_keywords()

    for article in articles:
        text = f"{article.get('title', '')} {article.get('summary', '')}".lower()
        if any(keyword in text for keyword in AVOID_KEYWORDS):
            continue

        score = int(article.get("credibility", 1)) * 10
        score += sum(4 for keyword in PRACTICAL_KEYWORDS if keyword in text)
        score += sum(8 for keyword in interest_keywords if keyword in text)

        perspective = article.get("perspective", "media")
        if perspective == "media":
            score += 8
        elif perspective == "builder":
            score += 5
        elif perspective == "official":
            score += 2

        published = article.get("published")
        if published:
            try:
                # Use JST for age calculation
                jst = timezone(timedelta(hours=9))
                age = datetime.now(jst) - datetime.fromisoformat(published)
                # Significantly boost fresh articles (less than 24h old)
                if age.days == 0:
                    score += 20
                else:
                    score += max(0, 5 - age.days)
            except Exception:
                pass

        article_with_score = dict(article)
        article_with_score["score"] = score
        scored_articles.append(article_with_score)

    scored_articles.sort(key=lambda item: item["score"], reverse=True)
    return pick_diverse_articles(scored_articles, limit=limit)


def pick_diverse_articles(
    scored_articles: list[dict[str, Any]],
    limit: int = 3,
) -> list[dict[str, Any]]:
    """Avoid a briefing where all 3 stories come from the same source."""
    selected = []
    used_sources = set()
    used_perspectives = set()

    for article in scored_articles:
        source = article.get("source", "")
        perspective = article.get("perspective", "")
        if source in used_sources:
            continue
        if len(selected) >= 2 and perspective in used_perspectives:
            continue

        selected.append(article)
        used_sources.add(source)
        used_perspectives.add(perspective)
        if len(selected) == limit:
            return selected

    for article in scored_articles:
        if article in selected:
            continue
        selected.append(article)
        if len(selected) == limit:
            break

    return selected


def load_interest_keywords() -> list[str]:
    """Optional personal tuning without adding settings screens or a database."""
    if not INTEREST_KEYWORDS_PATH.exists():
        return []

    keywords = []
    for line in INTEREST_KEYWORDS_PATH.read_text(encoding="utf-8").splitlines():
        keyword = line.strip().lower()
        if not keyword or keyword.startswith("#"):
            continue
        keywords.append(keyword)

    return keywords
