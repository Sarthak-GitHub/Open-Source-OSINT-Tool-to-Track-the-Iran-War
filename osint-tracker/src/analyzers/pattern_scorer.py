"""
Pattern Scorer
───────────────
Produces a weighted composite score from all anomaly signals.
Score range: 0.0 (normal) to 10.0 (maximum activity detected).
"""


class PatternScorer:
    def __init__(self, anomalies: dict, weights: dict):
        self.anomalies = anomalies
        self.weights = weights

    def score(self) -> dict:
        scores = {}

        for key in ("internet", "acled", "news", "aircraft"):
            signal = self.anomalies.get(key, {})
            normalised = signal.get("normalised", 0.0)
            scores[key] = round(normalised * 10, 2)

        # Weighted composite
        w = self.weights
        composite = (
            scores.get("internet", 0) * w.get("internet", 0.30) +
            scores.get("acled", 0)    * w.get("acled", 0.30) +
            scores.get("news", 0)     * w.get("news", 0.20) +
            scores.get("aircraft", 0) * w.get("aircraft", 0.20)
        )

        scores["composite"] = round(composite, 2)
        scores["status"] = self._status(composite)
        scores["anomalies"] = self.anomalies

        return scores

    def _status(self, score: float) -> str:
        if score >= 7.0:
            return "🔴 HIGH ACTIVITY DETECTED"
        elif score >= 4.0:
            return "🟡 ELEVATED ACTIVITY"
        elif score >= 2.0:
            return "🟠 WATCH — ABOVE BASELINE"
        return "🟢 NORMAL"
