"""
Aircraft Movement Collector
─────────────────────────────
Uses OpenSky Network API — the free, open-source ADS-B flight tracker.

OpenSky Network aggregates ADS-B data from a worldwide network of receivers
and makes it available via a free API (no charge even for high-volume use).

Unlike some paid flight trackers, OpenSky does NOT remove aircraft at 
government request. This means military and sensitive government flights 
that vanish from other trackers often still appear here.

What we look for:
- Unusual density of flights in a bounding box
- Aircraft with military callsign patterns
- Known military aircraft types (tankers, ISR, AWACS)
- Abnormal routing or flight behavior

Real OSINT analysts tracked US ISR flights using exactly this technique.

API docs: https://opensky-network.org/apidoc
Registration: https://opensky-network.org/community/register/opensky (free)
"""

import aiohttp
import os
import logging
from datetime import datetime
from base64 import b64encode
from .base_collector import BaseCollector

logger = logging.getLogger(__name__)

# ICAO hex prefixes for military/government aircraft by country (examples)
MILITARY_HEX_PREFIXES = {
    "US": ["ADF", "AE"],      # USAF, USN
    "Israel": ["738", "739"],  # Israeli AF
    "UK": ["43C", "43D"],     # RAF
}

# Aircraft types and callsign patterns that indicate special missions
ISR_CALLSIGNS = {
    "RC135": "SIGINT/Reconnaissance",
    "KC135": "Air-to-Air Refuelling (indicates extended ops)",
    "E3": "AWACS (airborne surveillance)",
    "P8": "Maritime patrol / ASW",
    "RQ4": "Global Hawk drone",
    "U2": "High-altitude reconnaissance",
    "E8": "JSTARS (ground surveillance)",
}

OPENSKY_BASE = "https://api.opensky-network.org"


class AircraftCollector(BaseCollector):
    name = "OpenSky Network Aircraft Signals"
    source_key = "aircraft"

    def __init__(self, region: dict, start_date: datetime, end_date: datetime, demo_mode: bool = False):
        super().__init__(region, start_date, end_date)
        self.demo_mode = demo_mode
        self.username = os.getenv("OPENSKY_USERNAME")
        self.password = os.getenv("OPENSKY_PASSWORD")

    async def _fetch(self) -> dict:
        """
        Query OpenSky Network for aircraft currently in the region's bounding box.
        Returns flight counts, notable aircraft types, and anomaly indicators.
        """
        if self.demo_mode or (not self.username and not self.password):
            logger.info("OpenSky: Demo mode or credentials missing, using demo data")
            return self._demo_data()

        bbox = self.region.get("bbox", [])
        if len(bbox) != 4:
            return self._empty_response()

        min_lat, min_lon, max_lat, max_lon = bbox

        # OpenSky API endpoint for states in bounding box
        url = f"{OPENSKY_BASE}/v2/states/all"
        params = {
            "lamin": min_lat,
            "lomin": min_lon,
            "lamax": max_lat,
            "lomax": max_lon,
        }

        headers = {}
        if self.username and self.password:
            # Create basic auth header for better rate limits
            auth_str = b64encode(f"{self.username}:{self.password}".encode()).decode()
            headers["Authorization"] = f"Basic {auth_str}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, params=params, headers=headers, 
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return self._parse_states(data.get("states", []))
                    else:
                        logger.warning(f"OpenSky API error {resp.status} — using demo data")
                        return self._demo_data()
        except Exception as e:
            logger.warning(f"OpenSky fetch failed: {e} — using demo data")
            return self._demo_data()

    def _parse_states(self, states_list: list) -> dict:
        """
        Analyze raw aircraft state list for notable patterns.
        
        State format: [icao24, callsign, origin_country, time_position, last_contact, 
                       lon, lat, baro_altitude, on_ground, velocity, true_track, 
                       vertical_rate, sensors, geo_altitude, squawk, spi, position_source]
        """
        if not states_list:
            return self._empty_response()

        total = len(states_list)
        military_spotted = []
        isr_spotted = []
        unusual_patterns = []

        for state in states_list:
            if not state or len(state) < 17:
                continue

            icao24 = (state[0] or "").upper()
            callsign = (state[1] or "").strip().upper()
            country = state[2] or "Unknown"
            lat = state[6]
            lon = state[5]
            altitude = state[7]
            on_ground = state[8]
            velocity = state[9]
            track = state[10]

            # Check military patterns
            for country_code, prefixes in MILITARY_HEX_PREFIXES.items():
                if any(icao24.startswith(p) for p in prefixes):
                    military_spotted.append({
                        "icao24": icao24,
                        "callsign": callsign,
                        "country": country,
                        "lat": lat,
                        "lon": lon,
                        "altitude": altitude,
                        "velocity": velocity,
                    })

            # Check for ISR/special mission callsigns
            for isr_type, mission in ISR_CALLSIGNS.items():
                if isr_type in callsign or isr_type in country:
                    isr_spotted.append({
                        "icao24": icao24,
                        "callsign": callsign,
                        "mission": mission,
                        "country": country,
                        "lat": lat,
                        "lon": lon,
                    })

            # Check for unusual patterns (e.g., high altitude, hovering)
            if altitude and altitude > 35000 and velocity and velocity < 100:
                unusual_patterns.append({
                    "icao24": icao24,
                    "callsign": callsign,
                    "pattern": "High altitude, low speed (possible ISR)",
                })

        return {
            "total_aircraft": total,
            "military_spotted": military_spotted,
            "isr_spotted": isr_spotted,
            "unusual_patterns": unusual_patterns,
            "count_military": len(military_spotted),
            "count_isr": len(isr_spotted),
            "anomaly_score": min(1.0, len(military_spotted) / max(1, total / 10)),
        }

    def _demo_data(self) -> dict:
        """Demo data simulating a military activity surge."""
        return {
            "total_aircraft": 47,
            "military_spotted": [
                {
                    "icao24": "ADF001",
                    "callsign": "MAGIC41",
                    "country": "United States",
                    "lat": 35.5,
                    "lon": 50.2,
                    "altitude": 28000,
                    "velocity": 420,
                },
                {
                    "icao24": "AE0042",
                    "callsign": "NAVY11",
                    "country": "United States",
                    "lat": 34.8,
                    "lon": 51.1,
                    "altitude": 24000,
                    "velocity": 380,
                },
            ],
            "isr_spotted": [
                {
                    "icao24": "ADF088",
                    "callsign": "RC135",
                    "mission": "SIGINT/Reconnaissance",
                    "country": "United States",
                    "lat": 35.2,
                    "lon": 50.8,
                },
            ],
            "unusual_patterns": [
                {
                    "icao24": "ADF123",
                    "callsign": "ARIES89",
                    "pattern": "High altitude, low speed (possible ISR)",
                }
            ],
            "count_military": 2,
            "count_isr": 1,
            "anomaly_score": 0.68,
            "_demo": True,
        }

    def _empty_response(self) -> dict:
        return {
            "total_aircraft": 0,
            "military_spotted": [],
            "isr_spotted": [],
            "unusual_patterns": [],
            "count_military": 0,
            "count_isr": 0,
            "anomaly_score": 0.0,
        }

    def summary(self) -> str:
        """Human-readable summary of aircraft findings."""
        if not self._result:
            return "No aircraft data collected"

        total = self._result.get("total_aircraft", 0)
        military = self._result.get("count_military", 0)
        isr = self._result.get("count_isr", 0)
        score = self._result.get("anomaly_score", 0.0)
        demo = self._result.get("_demo", False)

        demo_marker = " [DEMO]" if demo else ""
        return (
            f"{total} aircraft tracked | "
            f"{military} military | "
            f"{isr} ISR missions | "
            f"Anomaly score: {score:.2f}{demo_marker}"
        )
