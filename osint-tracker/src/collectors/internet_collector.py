"""
Internet Outage Collector
─────────────────────────
Uses the IODA (Internet Outage Detection & Analysis) API from Georgia Tech.
Completely free, no API key required.

IODA monitors global internet connectivity in near real-time by measuring:
- BGP routing changes
- Active probing (ping-based)
- Darknet telescope data (unsolicited traffic to unused IPs)

When a country's connectivity collapses, it often precedes or coincides
with physical conflict — as was seen with Iran on Feb 28, 2026,
when connectivity dropped to ~4% of normal levels.

API docs: https://ioda.live/api
"""

import aiohttp
import logging
from datetime import datetime
from .base_collector import BaseCollector

logger = logging.getLogger(__name__)

IODA_BASE = "https://api.ioda.caida.org/v2"


class InternetCollector(BaseCollector):
    name = "IODA Internet Outage Data"
    source_key = "internet"

    def __init__(self, region: dict, start_date: datetime, end_date: datetime, demo_mode: bool = False):
        super().__init__(region, start_date, end_date, demo_mode=demo_mode)
        # Note: IODA has no API key, so demo_mode doesn't affect functionality

    async def _fetch(self) -> dict:
        """
        Fetch internet outage signals for the target country from IODA.
        Returns time-series connectivity data with anomaly scores.
        """
        country = self.region.get("acled_country", "Iran")

        # IODA uses ISO country names — map common ones
        country_map = {
            "Iran": "IR",
            "Israel": "IL",
            "United Arab Emirates": "AE",
            "Qatar": "QA",
            "Bahrain": "BH",
        }
        iso_code = country_map.get(country, country[:2].upper())

        start_ts = int(self.start_date.timestamp())
        end_ts = int(self.end_date.timestamp())

        url = (
            f"{IODA_BASE}/signals/raw/country/{iso_code}"
            f"?from={start_ts}&until={end_ts}&datasource=bgp,ping-slash24,ucsd-nt"
        )

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status != 200:
                        logger.warning(f"IODA returned {resp.status} for {iso_code}")
                        return self._empty_response(iso_code)

                    raw = await resp.json()
        except Exception as e:
            logger.warning(f"IODA API error: {e}")
            return self._empty_response(iso_code)

        return self._parse_response(raw, iso_code)

    def _parse_response(self, raw: dict, iso_code: str) -> dict:
        """
        Extract connectivity time-series and compute a normalised outage score.

        Score logic:
          - Baseline = median value over first 20% of the time window
          - Outage score = how far current drops below baseline
          - 0.0 = normal connectivity
          - 1.0 = complete outage
        """
        series = []
        min_val = None
        baseline = None

        try:
            data_points = raw.get("data", {})
            bgp_series = data_points.get("bgp", {}).get("values", [])

            if bgp_series:
                values = [v for v in bgp_series if v is not None]
                if values:
                    baseline_window = values[:max(1, len(values) // 5)]
                    baseline = sum(baseline_window) / len(baseline_window)
                    min_val = min(values)

                    series = [
                        {
                            "timestamp": self.start_date.timestamp() + i * 300,  # 5-min intervals
                            "value": v,
                            "normalised": v / baseline if baseline > 0 else 1.0,
                        }
                        for i, v in enumerate(values)
                    ]

            outage_score = 0.0
            if baseline and min_val is not None and baseline > 0:
                drop_fraction = (baseline - min_val) / baseline
                outage_score = min(1.0, max(0.0, drop_fraction))

        except Exception as e:
            logger.error(f"Error parsing IODA response: {e}")
            outage_score = 0.0
            series = []

        return {
            "country_iso": iso_code,
            "series": series,
            "baseline": baseline,
            "min_observed": min_val,
            "outage_score": outage_score,
            "data_points": len(series),
        }

    def _empty_response(self, iso_code: str) -> dict:
        return {
            "country_iso": iso_code,
            "series": [],
            "baseline": None,
            "min_observed": None,
            "outage_score": 0.0,
            "data_points": 0,
        }

    def summary(self) -> str:
        if not self._result:
            return "No data"
        score = self._result.get("outage_score", 0)
        pts = self._result.get("data_points", 0)
        level = "🔴 SEVERE" if score > 0.5 else "🟡 PARTIAL" if score > 0.2 else "🟢 NORMAL"
        return f"{pts} data points | Outage score: {score:.2f} | {level}"
