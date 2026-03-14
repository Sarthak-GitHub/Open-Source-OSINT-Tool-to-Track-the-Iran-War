"""
News Signal Collector
──────────────────────
Uses NewsAPI to track keyword volume and sentiment in news coverage.
Free tier: 100 requests/day — sufficient for monitoring.

The insight: news volume *velocity* is often a leading indicator.
When keyword mentions spike 3-5x in 24 hours, something has changed
on the ground before official statements confirm it.

This is how Bellingcat and other OSINT researchers detected the
early stages of conflicts — by watching what reporters were filing
before governments acknowledged anything.

API docs: https://newsapi.org/docs
"""

import aiohttp
import os
import logging
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from .base_collector import BaseCollector

logger = logging.getLogger(__name__)

NEWSAPI_BASE = "https://newsapi.org/v2/everything"


class NewsCollector(BaseCollector):
    name = "NewsAPI Keyword Signals"
    source_key = "news"

    async def _fetch(self) -> dict:
        api_key = os.getenv("NEWS_API_KEY")

        if self.demo_mode or not api_key:
            source = "demo mode" if self.demo_mode else "missing API key"
            logger.warning(f"NewsAPI: {source} — using demo data")
            return self._demo_data()

        keywords = self.region.get("news_keywords", [])
        if not keywords:
            return self._empty_response()

        # Build OR query from region keywords
        query = " OR ".join(f'"{kw}"' for kw in keywords[:5])

        params = {
            "q": query,
            "from": self.start_date.strftime("%Y-%m-%d"),
            "to": self.end_date.strftime("%Y-%m-%d"),
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 100,
            "apiKey": api_key,
        }

        articles = []
        async with aiohttp.ClientSession() as session:
            async with session.get(
                NEWSAPI_BASE, params=params, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    articles = data.get("articles", [])
                else:
                    logger.error(f"NewsAPI error {resp.status}")
                    return self._demo_data()

        return self._parse_articles(articles)

    def _parse_articles(self, articles: list) -> dict:
        """
        Parse news articles into:
        - Volume time-series (articles per day)
        - Source diversity (how many different outlets)
        - Keyword frequency within articles
        - Volume spike score (vs. baseline period)
        """
        by_date = Counter()
        sources = set()
        keyword_hits = Counter()

        for article in articles:
            published = article.get("publishedAt", "")[:10]
            source = article.get("source", {}).get("name", "Unknown")
            title = (article.get("title") or "").lower()
            description = (article.get("description") or "").lower()
            content = title + " " + description

            by_date[published] += 1
            sources.add(source)

            # Track which keywords appear most
            for kw in self.region.get("news_keywords", []):
                if kw.lower() in content:
                    keyword_hits[kw] += 1

        # Compute spike score: compare last 2 days vs earlier baseline
        sorted_dates = sorted(by_date.keys())
        if len(sorted_dates) >= 3:
            baseline_dates = sorted_dates[:-2]
            spike_dates = sorted_dates[-2:]
            baseline_avg = sum(by_date[d] for d in baseline_dates) / len(baseline_dates)
            spike_avg = sum(by_date[d] for d in spike_dates) / len(spike_dates)
            spike_multiplier = spike_avg / baseline_avg if baseline_avg > 0 else 1.0
        else:
            spike_multiplier = 1.0

        return {
            "total_articles": len(articles),
            "by_date": dict(by_date),
            "source_count": len(sources),
            "top_keywords": dict(keyword_hits.most_common(5)),
            "spike_multiplier": round(spike_multiplier, 2),
            "sources_sample": list(sources)[:10],
        }

    def _demo_data(self) -> dict:
        return {
            "total_articles": 847,
            "by_date": {
                "2026-02-24": 23,
                "2026-02-25": 31,
                "2026-02-26": 45,
                "2026-02-27": 89,
                "2026-02-28": 412,
                "2026-03-01": 247,
            },
            "source_count": 94,
            "top_keywords": {
                "Iran military": 312,
                "Operation Epic Fury": 287,
                "IRGC": 198,
                "Tehran strike": 176,
                "Iran nuclear": 143,
            },
            "spike_multiplier": 9.2,
            "sources_sample": ["Reuters", "BBC", "AP", "Al Jazeera", "NYT", "Guardian"],
            "_demo": True,
        }

    def _empty_response(self) -> dict:
        return {
            "total_articles": 0,
            "by_date": {},
            "source_count": 0,
            "top_keywords": {},
            "spike_multiplier": 1.0,
            "sources_sample": [],
        }

    def summary(self) -> str:
        if not self._result:
            return "No data"
        total = self._result.get("total_articles", 0)
        sources = self._result.get("source_count", 0)
        spike = self._result.get("spike_multiplier", 1.0)
        demo = " [DEMO]" if self._result.get("_demo") else ""
        return f"{total} articles | {sources} sources | Volume spike: {spike}x{demo}"
