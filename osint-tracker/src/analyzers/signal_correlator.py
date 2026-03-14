"""
Signal Correlator
──────────────────
Merges signals from all four collectors into a unified timeline.

The key insight of OSINT correlation: no single signal is conclusive.
But when internet connectivity drops 80% AND conflict events spike 340%
AND ISR aircraft appear on flight trackers AND news volume goes 9x —
that composite picture tells a story that's hard to refute.

This is exactly how researchers at Bellingcat, CNAS, and academic
institutions pieced together the early hours of Operation Epic Fury
on February 28, 2026 — before any official confirmation.
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class SignalCorrelator:
    """
    Takes raw collector outputs and produces a unified signal dictionary
    suitable for anomaly detection and scoring.
    """

    def __init__(self, results: dict, thresholds: dict):
        self.results = results
        self.thresholds = thresholds

    def correlate(self) -> dict:
        """
        Produce a normalised signal dict from all collector outputs.
        Each signal is normalised to a 0.0–1.0 scale for comparison.
        """
        correlated = {}

        # Internet signal
        internet = self.results.get("internet") or {}
        correlated["internet"] = {
            "raw_score": internet.get("outage_score", 0.0),
            "normalised": internet.get("outage_score", 0.0),  # Already 0–1
            "data_points": internet.get("data_points", 0),
            "series": internet.get("series", []),
        }

        # Conflict signal
        acled = self.results.get("acled") or {}
        explosion_count = acled.get("explosion_count", 0)
        # Normalise: 0 events = 0.0, 50+ events = 1.0
        acled_normalised = min(1.0, explosion_count / 50.0)
        correlated["acled"] = {
            "raw_score": explosion_count,
            "normalised": acled_normalised,
            "total_events": acled.get("total_events", 0),
            "fatalities": acled.get("total_fatalities", 0),
            "hotspots": acled.get("hotspots", []),
            "geo_points": acled.get("geo_points", []),
            "events_by_date": acled.get("events_by_date", {}),
        }

        # News signal
        news = self.results.get("news") or {}
        spike = news.get("spike_multiplier", 1.0)
        # Normalise: 1x = 0.0, 10x+ = 1.0
        news_normalised = min(1.0, (spike - 1.0) / 9.0)
        correlated["news"] = {
            "raw_score": spike,
            "normalised": max(0.0, news_normalised),
            "total_articles": news.get("total_articles", 0),
            "source_count": news.get("source_count", 0),
            "top_keywords": news.get("top_keywords", {}),
            "by_date": news.get("by_date", {}),
        }

        # Aircraft signal
        aircraft = self.results.get("aircraft") or {}
        military_count = aircraft.get("military_count", 0)
        isr_count = aircraft.get("isr_count", 0)
        # Normalise: 0 = 0.0, 15+ military or 5+ ISR = 1.0
        aircraft_normalised = min(1.0, (military_count / 15.0) + (isr_count / 5.0))
        correlated["aircraft"] = {
            "raw_score": military_count,
            "normalised": min(1.0, aircraft_normalised),
            "total_tracked": aircraft.get("total_aircraft", 0),
            "military_count": military_count,
            "isr_count": isr_count,
            "isr_spotted": aircraft.get("isr_spotted", []),
        }

        return correlated
