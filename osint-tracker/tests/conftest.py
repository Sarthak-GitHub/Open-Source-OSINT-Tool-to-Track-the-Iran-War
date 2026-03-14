"""
conftest.py — Shared pytest fixtures and helpers.

All tests use these fixtures so no test ever makes a real API call.
This keeps the test suite fast, deterministic, and CI-friendly.
"""

import json
import pytest
from pathlib import Path
from datetime import datetime, timedelta

FIXTURES_DIR = Path(__file__).parent / "fixtures"

# ── Shared region config used across all tests ──────────────────────────────

@pytest.fixture
def iran_region():
    return {
        "name": "Iran",
        "bbox": [25.0, 44.0, 39.8, 63.3],
        "center": [32.4, 53.7],
        "acled_country": "Iran",
        "news_keywords": ["Iran military", "IRGC", "Tehran strike", "Iran nuclear"],
        "internet_asns": ["AS48159", "AS197207"],
    }


@pytest.fixture
def date_range():
    end = datetime(2026, 2, 28, 22, 0, 0)
    start = end - timedelta(days=7)
    return start, end


# ── Fixture file loader ──────────────────────────────────────────────────────

def load_fixture(filename: str) -> dict:
    """
    Load a JSON fixture file from tests/fixtures/.

    Usage in tests:
        from conftest import load_fixture
        data = load_fixture("ioda_outage.json")
    """
    path = FIXTURES_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Fixture not found: {path}\n"
            f"Available fixtures: {[f.name for f in FIXTURES_DIR.glob('*.json')]}"
        )
    with open(path) as f:
        return json.load(f)


# ── Pre-loaded fixture fixtures ───────────────────────────────────────────────

@pytest.fixture
def ioda_normal():
    return load_fixture("ioda_normal.json")


@pytest.fixture
def ioda_outage():
    return load_fixture("ioda_outage.json")


@pytest.fixture
def acled_quiet():
    return load_fixture("acled_quiet.json")


@pytest.fixture
def acled_conflict():
    return load_fixture("acled_conflict.json")


@pytest.fixture
def newsapi_baseline():
    return load_fixture("newsapi_baseline.json")


@pytest.fixture
def newsapi_spike():
    return load_fixture("newsapi_spike.json")


# ── Config fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def thresholds():
    return {
        "internet_outage_percent": 20,
        "news_volume_spike_multiplier": 3.0,
        "acled_event_spike_percent": 50,
        "flight_count_spike_percent": 40,
    }


@pytest.fixture
def scoring_weights():
    return {
        "internet": 0.30,
        "acled":    0.30,
        "news":     0.20,
        "aircraft": 0.20,
    }
