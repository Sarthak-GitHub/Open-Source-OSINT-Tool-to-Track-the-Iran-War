#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# OSINT Tracker — Container Entrypoint
#
# Runs before main.py to:
# 1. Validate environment
# 2. Warn about missing API keys
# 3. Show which data sources are live vs demo
# ─────────────────────────────────────────────────────────────────

set -e

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🛰️  OSINT Tracker"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ── Check API keys and report status ──────────────────────────────
echo "  Data Source Status:"
echo "  ───────────────────────────────────────────"

# IODA — always available, no key needed
echo "  ✅  IODA (Internet Outage)     — live (no key needed)"

# ACLED
if [ -n "$ACLED_API_KEY" ] && [ -n "$ACLED_EMAIL" ]; then
    echo "  ✅  ACLED (Conflict Events)    — live (key found)"
else
    echo "  ⚠️   ACLED (Conflict Events)    — demo mode (no key)"
fi

# NewsAPI
if [ -n "$NEWS_API_KEY" ]; then
    echo "  ✅  NewsAPI (News Signals)     — live (key found)"
else
    echo "  ⚠️   NewsAPI (News Signals)     — demo mode (no key)"
fi

# ADS-B Exchange
echo "  ✅  ADS-B Exchange (Aircraft)  — live (public feed)"

echo "  ───────────────────────────────────────────"
echo ""

# ── Warn if running fully on demo data ───────────────────────────
if [ -z "$ACLED_API_KEY" ] && [ -z "$NEWS_API_KEY" ]; then
    echo "  ℹ️  Running in FULL DEMO MODE"
    echo "     Results are realistic but not live."
    echo "     Add API keys to .env for real data."
    echo "     See docker/QUICKSTART.md for instructions."
    echo ""
fi

# ── Ensure data directories exist ────────────────────────────────
mkdir -p /app/data/raw /app/data/processed

# ── Hand off to main Python CLI ──────────────────────────────────
exec python main.py "$@"
