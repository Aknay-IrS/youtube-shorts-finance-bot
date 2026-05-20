"""
trend_detector.py
Finds trending finance topics using Google Trends + YouTube + Reddit.
All free — no paid APIs needed.
"""

import random
import logging
from datetime import datetime

import requests
from pytrends.request import TrendReq

import config

log = logging.getLogger(__name__)


def get_google_trends() -> list[str]:
    """Fetch trending finance searches on Google Trends (India)."""
    try:
        pt = TrendReq(hl="en-IN", tz=330, timeout=(10, 25))
        keywords = [
            "mutual fund", "stock market", "personal finance",
            "how to save money", "investment tips"
        ]
        pt.build_payload(keywords, cat=7, timeframe="now 1-d", geo="IN")
        related = pt.related_queries()

        topics = []
        for kw in keywords:
            df = related.get(kw, {}).get("top")
            if df is not None and not df.empty:
                topics += df["query"].head(3).tolist()

        log.info(f"Google Trends found {len(topics)} topics")
        return topics[:10]
    except Exception as e:
        log.warning(f"Google Trends failed: {e} — using fallback")
        return []


def get_youtube_trending_finance() -> list[str]:
    """Find trending finance Shorts titles on YouTube."""
    if not config.PEXELS_API_KEY:
        return []
    try:
        # YouTube Data API — search for trending finance Shorts
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": "finance money tips India #shorts",
            "type": "video",
            "videoDuration": "short",
            "order": "viewCount",
            "regionCode": "IN",
            "relevanceLanguage": "en",
            "maxResults": 10,
            "key": config.CLAUDE_API_KEY,  # use YT key if separate
        }
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            items = r.json().get("items", [])
            titles = [i["snippet"]["title"] for i in items]
            log.info(f"YouTube found {len(titles)} trending titles")
            return titles
    except Exception as e:
        log.warning(f"YouTube trending failed: {e}")
    return []


def get_reddit_trending() -> list[str]:
    """Scrape top posts from Indian finance subreddits (no API key needed)."""
    subreddits = [
        "IndiaInvestments", "personalfinanceindia",
        "IndianStockMarket", "DalalStreetTalks"
    ]
    topics = []
    headers = {"User-Agent": "Mozilla/5.0 (FinanceBot/1.0)"}

    for sub in subreddits[:2]:   # limit to 2 to avoid rate limits
        try:
            url = f"https://www.reddit.com/r/{sub}/hot.json?limit=5"
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                posts = r.json()["data"]["children"]
                for p in posts:
                    title = p["data"]["title"]
                    if len(title) > 10:
                        topics.append(title)
        except Exception as e:
            log.warning(f"Reddit {sub} failed: {e}")

    log.info(f"Reddit found {len(topics)} topics")
    return topics


def pick_best_topic(trends: list[str], used_today: list[str]) -> str:
    """
    Pick the best topic from trends.
    Falls back to config.FINANCE_TOPICS if no trends found.
    Avoids repeating topics used today.
    """
    all_topics = trends + config.FINANCE_TOPICS

    # Filter out already used today
    available = [t for t in all_topics if t not in used_today]
    if not available:
        available = config.FINANCE_TOPICS   # reset if all used

    # Prefer shorter, punchy topics (better for Shorts hooks)
    scored = sorted(available, key=lambda t: (
        -min(len(t.split()), 8),   # prefer 4-8 word topics
        random.random()             # small random factor for variety
    ))

    chosen = scored[0]
    log.info(f"Chosen topic: {chosen}")
    return chosen


def get_trending_topic(used_today: list[str] = None) -> str:
    """Main entry point — returns the best trending finance topic."""
    if used_today is None:
        used_today = []

    log.info("Fetching trending topics...")

    # Gather from all sources
    google   = get_google_trends()
    reddit   = get_reddit_trending()
    combined = google + reddit

    topic = pick_best_topic(combined, used_today)
    return topic


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(get_trending_topic())
