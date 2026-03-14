"""
Tests for OSINT signal analyzers — correlator, anomaly detector, scorer.
"""

import pytest
from src.analyzers.signal_correlator import SignalCorrelator
from src.analyzers.anomaly_detector import AnomalyDetector
from src.analyzers.pattern_scorer import PatternScorer

THRESHOLDS = {
    "internet_outage_percent": 20,
    "news_volume_spike_multiplier": 3.0,
    "acled_event_spike_percent": 50,
    "flight_count_spike_percent": 40,
}

WEIGHTS = {
    "internet": 0.30,
    "acled": 0.30,
    "news": 0.20,
    "aircraft": 0.20,
}

# Simulate a high-activity scenario (Iran Feb 28 2026 style)
HIGH_ACTIVITY_RESULTS = {
    "internet": {
        "outage_score": 0.91,
        "data_points": 288,
        "series": [],
        "baseline": 1000,
        "min_observed": 90,
    },
    "acled": {
        "total_events": 47,
        "explosion_count": 40,
        "total_fatalities": 234,
        "hotspots": [{"location": "Tehran", "count": 12}],
        "geo_points": [],
        "events_by_date": {"2026-02-28": 40},
    },
    "news": {
        "total_articles": 847,
        "spike_multiplier": 9.2,
        "source_count": 94,
        "top_keywords": {"Iran military": 312},
        "by_date": {},
    },
    "aircraft": {
        "total_aircraft": 34,
        "military_count": 12,
        "isr_count": 4,
        "military_spotted": [],
        "isr_spotted": [],
        "emergency_squawks": [],
    },
}

# Simulate a quiet/normal scenario
QUIET_RESULTS = {
    "internet": {"outage_score": 0.02, "data_points": 288, "series": [], "baseline": 1000, "min_observed": 980},
    "acled": {"total_events": 2, "explosion_count": 1, "total_fatalities": 0, "hotspots": [], "geo_points": [], "events_by_date": {}},
    "news": {"total_articles": 12, "spike_multiplier": 1.1, "source_count": 8, "top_keywords": {}, "by_date": {}},
    "aircraft": {"total_aircraft": 5, "military_count": 0, "isr_count": 0, "military_spotted": [], "isr_spotted": [], "emergency_squawks": []},
}


class TestSignalCorrelator:
    def test_high_activity_normalises_correctly(self):
        correlator = SignalCorrelator(HIGH_ACTIVITY_RESULTS, THRESHOLDS)
        result = correlator.correlate()

        assert result["internet"]["normalised"] > 0.8
        assert result["acled"]["normalised"] > 0.7
        assert result["news"]["normalised"] > 0.8
        assert result["aircraft"]["normalised"] > 0.5

    def test_quiet_activity_normalises_low(self):
        correlator = SignalCorrelator(QUIET_RESULTS, THRESHOLDS)
        result = correlator.correlate()

        assert result["internet"]["normalised"] < 0.1
        assert result["acled"]["normalised"] < 0.1
        assert result["news"]["normalised"] < 0.1

    def test_all_keys_present(self):
        correlator = SignalCorrelator(HIGH_ACTIVITY_RESULTS, THRESHOLDS)
        result = correlator.correlate()
        for key in ("internet", "acled", "news", "aircraft"):
            assert key in result
            assert "normalised" in result[key]
            assert "raw_score" in result[key]

    def test_normalised_values_bounded_0_to_1(self):
        correlator = SignalCorrelator(HIGH_ACTIVITY_RESULTS, THRESHOLDS)
        result = correlator.correlate()
        for key in ("internet", "acled", "news", "aircraft"):
            val = result[key]["normalised"]
            assert 0.0 <= val <= 1.0, f"{key} normalised value {val} out of bounds"


class TestAnomalyDetector:
    def test_high_activity_triggers_anomalies(self):
        correlator = SignalCorrelator(HIGH_ACTIVITY_RESULTS, THRESHOLDS)
        correlated = correlator.correlate()
        detector = AnomalyDetector(correlated, THRESHOLDS)
        anomalies = detector.detect()

        assert anomalies["internet"]["is_anomaly"] is True
        assert anomalies["acled"]["is_anomaly"] is True
        assert anomalies["news"]["is_anomaly"] is True

    def test_quiet_activity_no_anomalies(self):
        correlator = SignalCorrelator(QUIET_RESULTS, THRESHOLDS)
        correlated = correlator.correlate()
        detector = AnomalyDetector(correlated, THRESHOLDS)
        anomalies = detector.detect()

        assert anomalies["internet"]["is_anomaly"] is False
        assert anomalies["acled"]["is_anomaly"] is False
        assert anomalies["news"]["is_anomaly"] is False

    def test_severity_levels(self):
        correlator = SignalCorrelator(HIGH_ACTIVITY_RESULTS, THRESHOLDS)
        correlated = correlator.correlate()
        detector = AnomalyDetector(correlated, THRESHOLDS)
        anomalies = detector.detect()

        valid_severities = {"NORMAL", "MODERATE", "HIGH", "CRITICAL"}
        for key in ("internet", "acled", "news", "aircraft"):
            assert anomalies[key]["severity"] in valid_severities

    def test_description_present(self):
        correlator = SignalCorrelator(HIGH_ACTIVITY_RESULTS, THRESHOLDS)
        correlated = correlator.correlate()
        detector = AnomalyDetector(correlated, THRESHOLDS)
        anomalies = detector.detect()

        for key in ("internet", "acled", "news", "aircraft"):
            assert "description" in anomalies[key]
            assert len(anomalies[key]["description"]) > 0


class TestPatternScorer:
    def test_high_activity_scores_above_7(self):
        correlator = SignalCorrelator(HIGH_ACTIVITY_RESULTS, THRESHOLDS)
        correlated = correlator.correlate()
        detector = AnomalyDetector(correlated, THRESHOLDS)
        anomalies = detector.detect()
        scorer = PatternScorer(anomalies, WEIGHTS)
        scores = scorer.score()

        assert scores["composite"] >= 7.0
        assert "HIGH ACTIVITY" in scores["status"]

    def test_quiet_scores_below_2(self):
        correlator = SignalCorrelator(QUIET_RESULTS, THRESHOLDS)
        correlated = correlator.correlate()
        detector = AnomalyDetector(correlated, THRESHOLDS)
        anomalies = detector.detect()
        scorer = PatternScorer(anomalies, WEIGHTS)
        scores = scorer.score()

        assert scores["composite"] < 2.0
        assert "NORMAL" in scores["status"]

    def test_composite_bounded_0_to_10(self):
        correlator = SignalCorrelator(HIGH_ACTIVITY_RESULTS, THRESHOLDS)
        correlated = correlator.correlate()
        detector = AnomalyDetector(correlated, THRESHOLDS)
        anomalies = detector.detect()
        scorer = PatternScorer(anomalies, WEIGHTS)
        scores = scorer.score()

        assert 0.0 <= scores["composite"] <= 10.0

    def test_individual_scores_present(self):
        correlator = SignalCorrelator(HIGH_ACTIVITY_RESULTS, THRESHOLDS)
        correlated = correlator.correlate()
        detector = AnomalyDetector(correlated, THRESHOLDS)
        anomalies = detector.detect()
        scorer = PatternScorer(anomalies, WEIGHTS)
        scores = scorer.score()

        for key in ("internet", "acled", "news", "aircraft", "composite"):
            assert key in scores
            assert isinstance(scores[key], (int, float))
