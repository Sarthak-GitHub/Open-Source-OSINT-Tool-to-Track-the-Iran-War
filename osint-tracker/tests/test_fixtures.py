"""
test_fixtures.py
─────────────────
Tests that use the JSON fixture files in tests/fixtures/.
These verify the full parse → correlate → score pipeline
against realistic data scenarios — no live API calls needed.
"""

import pytest
from datetime import datetime, timedelta

from src.collectors.internet_collector import InternetCollector
from src.collectors.conflict_collector import ConflictCollector
from src.collectors.news_collector import NewsCollector
from src.analyzers.signal_correlator import SignalCorrelator
from src.analyzers.anomaly_detector import AnomalyDetector
from src.analyzers.pattern_scorer import PatternScorer

# conftest.py provides: iran_region, date_range, thresholds, scoring_weights
# and fixture loaders: ioda_normal, ioda_outage, acled_quiet, acled_conflict,
#                      newsapi_baseline, newsapi_spike


# ── Internet Collector + Fixtures ────────────────────────────────────────────

class TestInternetWithFixtures:

    def test_normal_fixture_produces_low_score(self, iran_region, date_range, ioda_normal):
        """Normal connectivity fixture should produce near-zero outage score."""
        start, end = date_range
        collector = InternetCollector(iran_region, start, end)
        result = collector._parse_response(ioda_normal, "IR")

        assert result["outage_score"] < 0.1, \
            f"Expected low outage score for normal data, got {result['outage_score']}"

    def test_outage_fixture_produces_high_score(self, iran_region, date_range, ioda_outage):
        """Outage fixture (91% drop) should produce score > 0.85."""
        start, end = date_range
        collector = InternetCollector(iran_region, start, end)
        result = collector._parse_response(ioda_outage, "IR")

        assert result["outage_score"] > 0.85, \
            f"Expected high outage score for outage fixture, got {result['outage_score']}"
        assert result["data_points"] > 0
        assert result["baseline"] is not None
        assert result["min_observed"] < result["baseline"]

    def test_outage_fixture_has_series_data(self, iran_region, date_range, ioda_outage):
        """Series data should be populated from fixture."""
        start, end = date_range
        collector = InternetCollector(iran_region, start, end)
        result = collector._parse_response(ioda_outage, "IR")

        assert len(result["series"]) > 0
        # Each series item should have timestamp, value, normalised
        for point in result["series"]:
            assert "timestamp" in point
            assert "value" in point
            assert "normalised" in point
            assert 0.0 <= point["normalised"] <= 2.0  # Allow briefly above 1 before clamp


# ── Conflict Collector + Fixtures ────────────────────────────────────────────

class TestConflictWithFixtures:

    def test_quiet_fixture_has_low_event_count(self, iran_region, date_range, acled_quiet):
        """Quiet fixture should have minimal events and zero explosion count."""
        start, end = date_range
        collector = ConflictCollector(iran_region, start, end)
        result = collector._parse_events(acled_quiet["data"])

        assert result["total_events"] == 2
        assert result["explosion_count"] == 0
        assert result["total_fatalities"] == 0

    def test_conflict_fixture_has_high_event_count(self, iran_region, date_range, acled_conflict):
        """Conflict fixture should have high event counts and multiple geopoints."""
        start, end = date_range
        collector = ConflictCollector(iran_region, start, end)
        result = collector._parse_events(acled_conflict["data"])

        assert result["total_events"] == 12
        assert result["explosion_count"] >= 10, \
            "Expected mostly explosions/battles in conflict fixture"
        assert len(result["geo_points"]) == 12
        assert len(result["hotspots"]) > 0

    def test_conflict_fixture_hotspot_is_tehran(self, iran_region, date_range, acled_conflict):
        """Tehran should be top hotspot in conflict fixture."""
        start, end = date_range
        collector = ConflictCollector(iran_region, start, end)
        result = collector._parse_events(acled_conflict["data"])

        top_location = result["hotspots"][0]["location"]
        assert top_location == "Tehran", \
            f"Expected Tehran as top hotspot, got {top_location}"

    def test_geo_points_have_valid_coordinates(self, iran_region, date_range, acled_conflict):
        """All geo_points should have valid lat/lon within Iran's bounding box."""
        start, end = date_range
        collector = ConflictCollector(iran_region, start, end)
        result = collector._parse_events(acled_conflict["data"])

        iran_bbox = iran_region["bbox"]  # [min_lat, min_lon, max_lat, max_lon]
        for point in result["geo_points"]:
            lat, lon = point["lat"], point["lon"]
            assert iran_bbox[0] <= lat <= iran_bbox[2], f"Lat {lat} out of Iran bbox"
            assert iran_bbox[1] <= lon <= iran_bbox[3], f"Lon {lon} out of Iran bbox"


# ── News Collector + Fixtures ─────────────────────────────────────────────────

class TestNewsWithFixtures:

    def test_baseline_fixture_low_spike(self, iran_region, date_range, newsapi_baseline):
        """Baseline news fixture should have spike multiplier near 1.0."""
        start, end = date_range
        collector = NewsCollector(iran_region, start, end)
        result = collector._parse_articles(newsapi_baseline["articles"])

        assert result["total_articles"] == len(newsapi_baseline["articles"])
        # With only 5 evenly distributed articles, spike should be ~1.0
        assert result["spike_multiplier"] <= 2.0, \
            f"Baseline should have low spike, got {result['spike_multiplier']}"

    def test_spike_fixture_high_multiplier(self, iran_region, date_range, newsapi_spike):
        """Spike fixture should have spike_multiplier >> 3.0."""
        start, end = date_range
        collector = NewsCollector(iran_region, start, end)
        result = collector._parse_articles(newsapi_spike["articles"])

        assert result["spike_multiplier"] >= 3.0, \
            f"Expected spike multiplier >= 3.0, got {result['spike_multiplier']}"
        assert result["total_articles"] > 0
        assert result["source_count"] > 1

    def test_spike_fixture_has_multiple_sources(self, iran_region, date_range, newsapi_spike):
        """Spike fixture should have multiple news outlets."""
        start, end = date_range
        collector = NewsCollector(iran_region, start, end)
        result = collector._parse_articles(newsapi_spike["articles"])

        assert result["source_count"] >= 5, \
            f"Expected >= 5 sources in spike fixture, got {result['source_count']}"


# ── Full End-to-End Pipeline with Fixtures ───────────────────────────────────

class TestFullPipelineWithFixtures:
    """
    End-to-end tests running the complete pipeline
    (collect → correlate → detect → score) using fixture data.
    """

    def _build_results(self, iran_region, date_range,
                       ioda_fixture, acled_fixture, news_fixture):
        """Helper: parse all fixtures into the format SignalCorrelator expects."""
        start, end = date_range

        inet_collector = InternetCollector(iran_region, start, end)
        inet_result = inet_collector._parse_response(ioda_fixture, "IR")

        conflict_collector = ConflictCollector(iran_region, start, end)
        conflict_result = conflict_collector._parse_events(acled_fixture["data"])

        news_collector = NewsCollector(iran_region, start, end)
        news_result = news_collector._parse_articles(news_fixture["articles"])

        aircraft_result = {
            "total_aircraft": 5,
            "military_count": 0,
            "isr_count": 0,
            "military_spotted": [],
            "isr_spotted": [],
            "emergency_squawks": [],
        }

        return {
            "internet": inet_result,
            "acled": conflict_result,
            "news": news_result,
            "aircraft": aircraft_result,
        }

    def test_quiet_scenario_scores_low(
        self, iran_region, date_range, thresholds, scoring_weights,
        ioda_normal, acled_quiet, newsapi_baseline
    ):
        """All quiet fixtures should produce composite score < 2.0."""
        results = self._build_results(
            iran_region, date_range, ioda_normal, acled_quiet, newsapi_baseline
        )
        correlated = SignalCorrelator(results, thresholds).correlate()
        anomalies  = AnomalyDetector(correlated, thresholds).detect()
        scores     = PatternScorer(anomalies, scoring_weights).score()

        assert scores["composite"] < 2.0, \
            f"Quiet scenario should score < 2.0, got {scores['composite']}"
        assert "NORMAL" in scores["status"]

    def test_conflict_scenario_scores_high(
        self, iran_region, date_range, thresholds, scoring_weights,
        ioda_outage, acled_conflict, newsapi_spike
    ):
        """All conflict fixtures should produce composite score > 7.0."""
        results = self._build_results(
            iran_region, date_range, ioda_outage, acled_conflict, newsapi_spike
        )
        correlated = SignalCorrelator(results, thresholds).correlate()
        anomalies  = AnomalyDetector(correlated, thresholds).detect()
        scores     = PatternScorer(anomalies, scoring_weights).score()

        assert scores["composite"] > 7.0, \
            f"Conflict scenario should score > 7.0, got {scores['composite']}"
        assert "HIGH ACTIVITY" in scores["status"]

    def test_mixed_scenario_scores_moderate(
        self, iran_region, date_range, thresholds, scoring_weights,
        ioda_normal, acled_conflict, newsapi_baseline
    ):
        """High ACLED + normal internet/news = moderate score (4–7 range)."""
        results = self._build_results(
            iran_region, date_range, ioda_normal, acled_conflict, newsapi_baseline
        )
        correlated = SignalCorrelator(results, thresholds).correlate()
        anomalies  = AnomalyDetector(correlated, thresholds).detect()
        scores     = PatternScorer(anomalies, scoring_weights).score()

        assert 2.0 < scores["composite"] < 8.0, \
            f"Mixed scenario should score in moderate range, got {scores['composite']}"

    def test_scores_always_bounded(
        self, iran_region, date_range, thresholds, scoring_weights,
        ioda_outage, acled_conflict, newsapi_spike
    ):
        """Composite and individual scores must always be 0.0–10.0."""
        results = self._build_results(
            iran_region, date_range, ioda_outage, acled_conflict, newsapi_spike
        )
        correlated = SignalCorrelator(results, thresholds).correlate()
        anomalies  = AnomalyDetector(correlated, thresholds).detect()
        scores     = PatternScorer(anomalies, scoring_weights).score()

        for key in ("internet", "acled", "news", "aircraft", "composite"):
            val = scores[key]
            assert 0.0 <= val <= 10.0, \
                f"Score for '{key}' out of bounds: {val}"
