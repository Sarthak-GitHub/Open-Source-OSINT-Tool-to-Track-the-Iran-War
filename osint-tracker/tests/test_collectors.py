"""
Tests for OSINT collectors.
Uses mock HTTP responses — no real API calls made during testing.
"""

import pytest
import responses as resp_mock
from datetime import datetime, timedelta
from src.collectors.internet_collector import InternetCollector
from src.collectors.conflict_collector import ConflictCollector
from src.collectors.news_collector import NewsCollector

REGION = {
    "name": "Iran",
    "bbox": [25.0, 44.0, 39.8, 63.3],
    "center": [32.4, 53.7],
    "acled_country": "Iran",
    "news_keywords": ["Iran military", "IRGC"],
    "internet_asns": ["AS48159"],
}

START = datetime.utcnow() - timedelta(days=7)
END = datetime.utcnow()


class TestInternetCollector:
    def test_empty_response_on_api_failure(self):
        collector = InternetCollector(REGION, START, END)
        result = collector._empty_response("IR")
        assert result["outage_score"] == 0.0
        assert result["data_points"] == 0
        assert result["country_iso"] == "IR"

    def test_parse_response_with_valid_data(self):
        collector = InternetCollector(REGION, START, END)
        mock_raw = {
            "data": {
                "bgp": {
                    "values": [100, 100, 95, 90, 20, 10, 5, 15, 20, 95, 100]
                }
            }
        }
        result = collector._parse_response(mock_raw, "IR")
        assert result["outage_score"] > 0
        assert result["data_points"] > 0
        assert result["baseline"] is not None
        # A drop from ~100 to ~5 should score highly
        assert result["outage_score"] > 0.5

    def test_parse_response_all_zeros(self):
        collector = InternetCollector(REGION, START, END)
        mock_raw = {"data": {"bgp": {"values": [0, 0, 0, 0]}}}
        result = collector._parse_response(mock_raw, "IR")
        assert result["outage_score"] == 0.0

    def test_summary_with_result(self):
        collector = InternetCollector(REGION, START, END)
        collector._result = {
            "outage_score": 0.85,
            "data_points": 288,
            "country_iso": "IR",
        }
        summary = collector.summary()
        assert "SEVERE" in summary
        assert "288" in summary


class TestConflictCollector:
    def test_demo_data_structure(self):
        collector = ConflictCollector(REGION, START, END)
        demo = collector._demo_data()
        assert "total_events" in demo
        assert "explosion_count" in demo
        assert "geo_points" in demo
        assert demo["explosion_count"] > 0
        assert all("lat" in pt and "lon" in pt for pt in demo["geo_points"])

    def test_parse_events_empty(self):
        collector = ConflictCollector(REGION, START, END)
        result = collector._parse_events([])
        assert result["total_events"] == 0
        assert result["explosion_count"] == 0

    def test_parse_events_counts_explosions(self):
        collector = ConflictCollector(REGION, START, END)
        mock_events = [
            {
                "event_type": "Explosions/Remote violence",
                "event_date": "2026-02-28",
                "location": "Tehran",
                "latitude": "35.6892",
                "longitude": "51.3890",
                "fatalities": "3",
                "notes": "Airstrike",
            },
            {
                "event_type": "Battles",
                "event_date": "2026-02-28",
                "location": "Isfahan",
                "latitude": "32.6546",
                "longitude": "51.6680",
                "fatalities": "0",
                "notes": "",
            },
            {
                "event_type": "Protests",
                "event_date": "2026-02-27",
                "location": "Tabriz",
                "latitude": "38.0000",
                "longitude": "46.2919",
                "fatalities": "0",
                "notes": "",
            },
        ]
        result = collector._parse_events(mock_events)
        assert result["total_events"] == 3
        assert result["explosion_count"] == 2  # Explosions + Battles
        assert result["total_fatalities"] == 3
        assert len(result["geo_points"]) == 3

    def test_summary_with_result(self):
        collector = ConflictCollector(REGION, START, END)
        collector._result = {
            "total_events": 47,
            "explosion_count": 31,
            "total_fatalities": 234,
        }
        summary = collector.summary()
        assert "47" in summary
        assert "31" in summary


class TestNewsCollector:
    def test_demo_data_has_spike(self):
        collector = NewsCollector(REGION, START, END)
        demo = collector._demo_data()
        assert demo["spike_multiplier"] > 3.0
        assert demo["total_articles"] > 0
        assert len(demo["top_keywords"]) > 0

    def test_parse_articles_empty(self):
        collector = NewsCollector(REGION, START, END)
        result = collector._parse_articles([])
        assert result["total_articles"] == 0
        assert result["spike_multiplier"] == 1.0

    def test_parse_articles_detects_spike(self):
        collector = NewsCollector(REGION, START, END)

        # Simulate: low baseline (days 1–5), huge spike on day 6–7
        articles = []
        for day in range(1, 6):
            for _ in range(5):  # 5 articles per baseline day
                articles.append({
                    "publishedAt": f"2026-02-{20+day}T12:00:00Z",
                    "source": {"name": "Reuters"},
                    "title": "Iran military news",
                    "description": "IRGC activity reported",
                })
        for _ in range(50):  # 50 articles on spike day
            articles.append({
                "publishedAt": "2026-02-28T12:00:00Z",
                "source": {"name": "BBC"},
                "title": "Iran military strike",
                "description": "Tehran strike reported",
            })

        result = collector._parse_articles(articles)
        assert result["total_articles"] == len(articles)
        assert result["spike_multiplier"] > 3.0
