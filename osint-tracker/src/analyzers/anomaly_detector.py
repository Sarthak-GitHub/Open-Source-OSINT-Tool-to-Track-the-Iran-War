"""
Anomaly Detector
──────────────────
Applies threshold-based anomaly flagging to correlated signals.
Keeps it simple — real anomaly detection doesn't need to be complex
when the signals are this different in magnitude from baseline.
"""

import logging

logger = logging.getLogger(__name__)


class AnomalyDetector:
    def __init__(self, correlated: dict, thresholds: dict):
        self.correlated = correlated
        self.thresholds = thresholds

    def detect(self) -> dict:
        anomalies = {}

        # Internet anomaly
        internet = self.correlated.get("internet", {})
        outage = internet.get("raw_score", 0.0)
        threshold_pct = self.thresholds.get("internet_outage_percent", 20) / 100
        anomalies["internet"] = {
            **internet,
            "is_anomaly": outage > threshold_pct,
            "severity": self._severity(outage, [0.2, 0.5, 0.8]),
            "description": self._internet_description(outage),
        }

        # ACLED anomaly
        acled = self.correlated.get("acled", {})
        norm = acled.get("normalised", 0.0)
        anomalies["acled"] = {
            **acled,
            "is_anomaly": norm > 0.2,
            "severity": self._severity(norm, [0.2, 0.5, 0.8]),
            "description": self._acled_description(acled.get("raw_score", 0)),
        }

        # News anomaly
        news = self.correlated.get("news", {})
        spike = news.get("raw_score", 1.0)
        threshold_mult = self.thresholds.get("news_volume_spike_multiplier", 3.0)
        anomalies["news"] = {
            **news,
            "is_anomaly": spike >= threshold_mult,
            "severity": self._severity(news.get("normalised", 0), [0.2, 0.5, 0.8]),
            "description": f"News volume {spike:.1f}x baseline",
        }

        # Aircraft anomaly
        aircraft = self.correlated.get("aircraft", {})
        norm_ac = aircraft.get("normalised", 0.0)
        anomalies["aircraft"] = {
            **aircraft,
            "is_anomaly": norm_ac > 0.2,
            "severity": self._severity(norm_ac, [0.2, 0.5, 0.8]),
            "description": self._aircraft_description(aircraft),
        }

        return anomalies

    def _severity(self, value: float, thresholds: list) -> str:
        low, med, high = thresholds
        if value >= high:
            return "CRITICAL"
        elif value >= med:
            return "HIGH"
        elif value >= low:
            return "MODERATE"
        return "NORMAL"

    def _internet_description(self, score: float) -> str:
        pct = int(score * 100)
        if score > 0.8:
            return f"Severe internet outage — {pct}% connectivity loss detected"
        elif score > 0.5:
            return f"Significant outage — {pct}% connectivity degradation"
        elif score > 0.2:
            return f"Partial outage — {pct}% connectivity drop"
        return "Connectivity within normal range"

    def _acled_description(self, count: int) -> str:
        if count > 40:
            return f"{count} explosions/battles — intensive conflict activity"
        elif count > 20:
            return f"{count} explosions/battles — elevated conflict activity"
        elif count > 5:
            return f"{count} explosions/battles — notable activity"
        return f"{count} conflict events recorded"

    def _aircraft_description(self, aircraft: dict) -> str:
        military = aircraft.get("military_count", 0)
        isr = aircraft.get("isr_count", 0)
        parts = []
        if isr > 0:
            parts.append(f"{isr} ISR/SIGINT aircraft")
        if military > 0:
            parts.append(f"{military} military flights")
        return " | ".join(parts) if parts else "No notable military aircraft"
