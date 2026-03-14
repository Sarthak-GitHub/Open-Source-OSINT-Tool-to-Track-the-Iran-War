"""
Conflict Events Collector
──────────────────────────
Uses the ACLED (Armed Conflict Location & Event Data) API.
Free for academic and research use — register at acleddata.com.

ACLED aggregates verified armed conflict events globally, including:
- Explosions / remote violence (airstrikes, shelling, drone attacks)
- Battles
- Protests and riots
- Strategic developments

This is the same data used by the UN, NGOs, and academic researchers
to track conflict patterns. When event counts spike, something is happening.

API docs: https://developer.acleddata.com
"""

import aiohttp
import os
import logging
from datetime import datetime
from collections import Counter
from .base_collector import BaseCollector

logger = logging.getLogger(__name__)

ACLED_BASE = "https://api.acleddata.com/acled/read"


class ConflictCollector(BaseCollector):
    name = "ACLED Conflict Events"
    source_key = "acled"

    async def _fetch(self) -> dict:
        """
        Fetch conflict events for the region from ACLED API.
        Groups events by type and date for anomaly scoring.
        """
        api_key = os.getenv("ACLED_API_KEY")
        email = os.getenv("ACLED_EMAIL")

        if self.demo_mode or not api_key or not email:
            source = "demo mode" if self.demo_mode else "missing credentials"
            logger.warning(f"ACLED: {source} — using demo data")
            return self._demo_data()

        country = self.region.get("acled_country", "Iran")
        params = {
            "key": api_key,
            "email": email,
            "country": country,
            "event_date": (
                f"{self.start_date.strftime('%Y-%m-%d')}|"
                f"{self.end_date.strftime('%Y-%m-%d')}"
            ),
            "event_date_where": "BETWEEN",
            "fields": "event_date|event_type|sub_event_type|location|latitude|longitude|fatalities|notes",
            "limit": 500,
            "format": "json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(
                ACLED_BASE, params=params, timeout=aiohttp.ClientTimeout(total=20)
            ) as resp:
                if resp.status != 200:
                    logger.error(f"ACLED API error: {resp.status}")
                    return self._demo_data()
                raw = await resp.json()

        return self._parse_events(raw.get("data", []))

    def _parse_events(self, events: list) -> dict:
        """
        Parse raw ACLED events into structured analysis data.

        Returns:
        - events_by_type: count breakdown by event category
        - events_by_date: daily event counts (for time-series)
        - hotspots: locations with most activity
        - fatalities: total reported fatalities
        - explosion_count: specifically tracks airstrikes + remote violence
        - raw_events: full list for map rendering
        """
        if not events:
            return self._empty_response()

        by_type = Counter()
        by_date = Counter()
        location_counts = Counter()
        total_fatalities = 0
        geo_points = []

        for event in events:
            etype = event.get("event_type", "Unknown")
            date = event.get("event_date", "")[:10]
            location = event.get("location", "Unknown")
            fatalities = int(event.get("fatalities", 0) or 0)
            lat = event.get("latitude")
            lon = event.get("longitude")

            by_type[etype] += 1
            by_date[date] += 1
            location_counts[location] += 1
            total_fatalities += fatalities

            if lat and lon:
                geo_points.append({
                    "lat": float(lat),
                    "lon": float(lon),
                    "type": etype,
                    "date": date,
                    "location": location,
                    "fatalities": fatalities,
                    "notes": event.get("notes", "")[:200],
                })

        explosion_count = (
            by_type.get("Explosions/Remote violence", 0)
            + by_type.get("Battles", 0)
        )

        hotspots = [
            {"location": loc, "count": count}
            for loc, count in location_counts.most_common(10)
        ]

        return {
            "total_events": len(events),
            "events_by_type": dict(by_type),
            "events_by_date": dict(by_date),
            "hotspots": hotspots,
            "total_fatalities": total_fatalities,
            "explosion_count": explosion_count,
            "geo_points": geo_points,
        }

    def _demo_data(self) -> dict:
        """
        Returns realistic demo data when no API key is configured.
        Based on publicly reported ACLED figures for the Iran region.
        """
        logger.info("Using ACLED demo data — set API keys for live data")
        return {
            "total_events": 47,
            "events_by_type": {
                "Explosions/Remote violence": 31,
                "Battles": 9,
                "Strategic developments": 5,
                "Protests": 2,
            },
            "events_by_date": {
                "2026-02-28": 18,
                "2026-02-27": 4,
                "2026-02-26": 3,
                "2026-02-25": 2,
            },
            "hotspots": [
                {"location": "Tehran", "count": 12},
                {"location": "Isfahan", "count": 8},
                {"location": "Natanz", "count": 6},
            ],
            "total_fatalities": 234,
            "explosion_count": 40,
            "geo_points": [
                {"lat": 35.6892, "lon": 51.3890, "type": "Explosions/Remote violence",
                 "date": "2026-02-28", "location": "Tehran", "fatalities": 0, "notes": "Airstrike reported"},
                {"lat": 32.6546, "lon": 51.6680, "type": "Explosions/Remote violence",
                 "date": "2026-02-28", "location": "Isfahan", "fatalities": 0, "notes": "Nuclear facility area"},
                {"lat": 33.7219, "lon": 51.8668, "type": "Explosions/Remote violence",
                 "date": "2026-02-28", "location": "Natanz", "fatalities": 0, "notes": "Enrichment site"},
            ],
            "_demo": True,
        }

    def _empty_response(self) -> dict:
        return {
            "total_events": 0,
            "events_by_type": {},
            "events_by_date": {},
            "hotspots": [],
            "total_fatalities": 0,
            "explosion_count": 0,
            "geo_points": [],
        }

    def summary(self) -> str:
        if not self._result:
            return "No data"
        total = self._result.get("total_events", 0)
        explosions = self._result.get("explosion_count", 0)
        fatalities = self._result.get("total_fatalities", 0)
        demo = " [DEMO]" if self._result.get("_demo") else ""
        return f"{total} events | {explosions} explosions/battles | {fatalities} fatalities reported{demo}"
