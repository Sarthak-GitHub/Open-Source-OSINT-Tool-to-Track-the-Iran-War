# OSINT Military Movement Tracker

> **Track geopolitical events using only public data, the same techniques used by Bellingcat, journalists, and open-source researchers worldwide.**

**Honest Status**: This is an **educational proof-of-concept**. Some data sources require API keys; this README tells you exactly which ones and what to expect without them.

---

## Disclaimer!

This tool uses **only legally and publicly available data sources**. It does not access any classified, private, or restricted information. All data sources used are open APIs, public feeds, and freely accessible databases. This project is strictly for **educational, research, and journalistic purposes**.

---

## 🔍 What It Does

OSINT Tracker is a Python pipeline that correlates signals from multiple public data sources to detect and visualize patterns of military/geopolitical activity:

| Layer | Data Source | What It Detects | Works Without API Key? |
|---|---|---|---|
| 🌐 **Internet** | IODA API (Georgia Tech) | Internet blackouts, connectivity drops | **YES** — Always works |
| 📰 **News Signals** | NewsAPI | Keyword surge detection in media coverage | **Free tier** — 2 min signup required |
| ✈️ **Aircraft** | OpenSky API | Military flight patterns, unusual activity | **Free tier** — Registration required |
| 📡 **Conflict Events** | ACLED API | Verified armed conflict events by location | **Demo mode only** — Approval takes 1-2 days |

When correlated together, these signals tell a story that no single source can.

---

### Data Source Reality Check

| Source | Free Tier | API Key | Time to Functional | Notes |
|--------|-----------|---------|-------------------|-------|
| **IODA** (Internet outages) | Full API | None | Immediately | 100% free, no registration |
| **NewsAPI** |Free tier | Quick signup | ~2 minutes | 100 requests/day, but sufficient for monitoring |
| **OpenSky Network** (Aircraft) | Free mode | Quick signup | ~2 minutes | Recently switched from ADS-B to this—works reliably |
| **ACLED** (Conflict events) | Demo only | Registration | 1–2 days | Approval required; demo data provided while waiting |

**TL;DR**: Clone the repo, run `python main.py --demo` **right now** with zero setup. Realistic OSINT requires one 5-minute signup (NewsAPI).

---

## Project Structure

```
osint-tracker/
├── src/
│   ├── collectors/
│   │   ├── __init__.py
│   │   ├── base_collector.py        # Shared interface + disk cache
│   │   ├── internet_collector.py    # IODA (always works)
│   │   ├── aircraft_collector.py    # OpenSky API (free tier)
│   │   ├── conflict_collector.py    # ACLED (demo mode fallback)
│   │   └── news_collector.py        # NewsAPI (free tier + demo)
│   ├── analyzers/
│   │   ├── __init__.py
│   │   ├── signal_correlator.py     # Cross-source signal correlation
│   │   ├── anomaly_detector.py      # Statistical anomaly detection
│   │   └── pattern_scorer.py        # Activity scoring engine
│   └── visualizers/
│       ├── __init__.py
│       ├── map_renderer.py          # Folium-based geo maps
│       └── dashboard.py            # Terminal dashboard
├── data/
│   ├── raw/                         # Raw API responses (auto-cached)
│   └── processed/                   # Final reports + maps
├── tests/
│   ├── test_collectors.py
│   ├── test_analyzers.py
│   └── fixtures/                    # Mock API responses
├── config/
│   └── regions.yaml                 # Regions of interest
├── scripts/
│   └── run_pipeline.sh             # Full pipeline runner
├── docs/
│   └── methodology.md              # OSINT tradecraft
├── main.py                          # CLI entry point
├── requirements.txt
├── .env.example
├── Dockerfile
└── docker-compose.yml
```

---

### Super Quick (No Setup)

Try the demo with cached real data from a recent conflict:

```bash
git clone git@github.com:Sarthak-GitHub/Open-Source-OSINT-Tool-to-Track-the-Iran-War.git
cd osint-tracker

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run on cached demo data (IODA + NewsAPI demo + ACLED demo)
python main.py --region iran --days 7 --demo
```

**What you get**: Real IODA internet outage data + simulated NewsAPI/ACLED to show correlation pipeline.

---

### For Realistic OSINT (5 min setup)

Get real data from IODA (always works) + real recent news coverage:

```bash
cp .env.example .env

# Edit .env and add your free NewsAPI key (2-min signup at newsapi.org)
nano .env

python main.py --region iran --days 7
```

**What you get**: Real data from IODA + NewsAPI. ACLED defaults to demo while waiting for approval.

---

### Full Setup (With All Sources)

1. Get your API keys:
   - **NewsAPI** (free): [newsapi.org](https://newsapi.org/register) — instant
   - **OpenSky** (free): [opensky-network.org](https://opensky-network.org/community/register/opensky) — instant
   - **ACLED** (free/academic): [acleddata.com](https://acleddata.com/dashboard) — 1–2 days for approval

2. Configure:
   ```bash
   cp .env.example .env
   nano .env
   # Fill in the keys
   ```

3. Run:
   ```bash
   python main.py --region iran --days 7
   ```

---

### Docker

```bash
docker-compose up --build

# Or with demo data:
docker run -e DEMO_MODE=1 osint-tracker python main.py --region iran --demo
```

---

## Configuration

### Environment Variables (`.env`)

```bash
# OPTIONAL — Free tier, get in 2 minutes
NEWS_API_KEY=your_newsapi_key_here

# OPTIONAL — Free tier, get in 2 minutes
OPENSKY_USERNAME=your_opensky_username
OPENSKY_PASSWORD=your_opensky_password

# OPTIONAL — Academic/research registration, 1-2 day wait
ACLED_API_KEY=your_acled_key_here
ACLED_EMAIL=your_email@example.com

# Always works (no key needed)
# IODA is public — no config required

# Output settings
OUTPUT_DIR=data/processed
RAW_CACHE_DIR=data/raw
CACHE_TTL_HOURS=6
LOG_LEVEL=INFO
```

### Running Options

```bash
# Demo mode — uses cached/synthetic data (no API keys needed)
python main.py --region iran --demo

# With real data (needs keys in .env)
python main.py --region iran --days 7

# Change output format
python main.py --region iran --output terminal    # Rich terminal dashboard
python main.py --region iran --output html        # Interactive map + JSON

# List available regions
python main.py --list-regions

# Different lookback window
python main.py --region strait_of_hormuz --days 30
```

---

## Graceful Degradation | Missing API Keys Don't Break Anything

If you don't have API keys set, the tool **doesn't crash**—it intelligently falls back:

```
$ python main.py --region iran --days 7

Collecting signals from public sources...
   IODA Internet Data — Real live data from Georgia Tech
   NewsAPI — Missing API key, using cached demo data
   ACLED Conflict — Missing credentials, using demo data
   OpenSky Aircraft — Missing credentials, skipping

═══════════════════════════════════════════════════
        OSINT TRACKER — SIGNAL REPORT
        Region: Iran  |  Period: Mar 7–14, 2026
═══════════════════════════════════════════════════

  LAYER              DATA SOURCE         SIGNAL             SCORE
  ──────────────────────────────────────────────────────────────
  Internet        IODA (real)      Connectivity ↓     8.3/10
  News            Demo cached     Keyword spike 4.2x  Synthetic/cached
  Conflict        Demo cached     Explosions +180     Synthetic/cached
  Aircraft        Requires key     (Skipped)           —

═══════════════════════════════════════════════════
  Legend: Real data |  Synthetic/cached | - Not available
═══════════════════════════════════════════════════
```

**Key advantage**: Start exploring OSINT concepts *immediately* with real IODA data. Add API keys as you go.

---

## Example Output (Full Setup)

```
═══════════════════════════════════════════════════════
        OSINT TRACKER — SIGNAL REPORT
        Region: Iran  |  Period: 2026-03-07 to 2026-03-14
═══════════════════════════════════════════════════════

  LAYER              SIGNAL             ANOMALY SCORE
  ─────────────────────────────────────────────────
  🌐 Internet        Connectivity drop   █████████ 9.1/10
  📰 News Volume     Keyword surge       ███████  7.4/10
  📡 ACLED Events    Explosions +340%    ████████ 8.7/10
  ✈️ Aircraft        Military flights    ████████ 8.2/10
  ─────────────────────────────────────────────────
  🔴 COMPOSITE SCORE                     ████████ 8.4/10
  STATUS: HIGH ACTIVITY DETECTED
═══════════════════════════════════════════════════════
Map saved to: data/processed/iran_20260314.html (interactive)
Raw JSON: data/processed/iran_20260314.json
```

---

## The Methodology

See [`docs/methodology.md`](docs/methodology.md) for a full explanation of:
- How OSINT analysts correlate multi-source signals
- The binary search approach to narrowing down events
- How Bellingcat tracked movements using only Google Maps and social media
- Ethical and legal boundaries of open-source research

---

## Inspiration & Credits

- [Bellingcat](https://www.bellingcat.com/) — the gold standard of OSINT journalism
- [ACLED](https://acleddata.com/) — Armed Conflict Location & Event Data Project
- [IODA](https://ioda.live/) — Internet Outage Detection & Analysis (Georgia Tech)
- [OpenSky Network](https://opensky-network.org/) — free ADS-B flight tracker API
- [NewsAPI](https://newsapi.org/) — global news aggregation with free tier

---

## FAQ

**Q: Can I really use this without paying?**  
A: Yes. IODA is 100% free. NewsAPI free tier (100 requests/day) is sufficient for monitoring. Add those two, and you have real signal correlation working.

**Q: Why does ACLED show demo data?**  
A: ACLED requires academic/research registration which takes 1–2 days for approval. While waiting, the tool shows you *what a real signal looks like* with demo data. Once your key arrives, replace it in `.env` and you get live event data.

**Q: What happened to ADS-B Exchange?**  
A: It was paywalled behind RapidAPI. We switched to OpenSky Network, which is 100% free and has a public API.

**Q: Can I run this in production?**  
A: This is an educational tool. For production OSINT, you'd want:
  - Persistent storage (PostgreSQL instead of JSON cache)
  - Scheduled pipelines (Airflow/Prefect)
  - Alerting on anomalies (webhooks, Slack integration)
  - Audit logging
  - See [SETUP.md](SETUP.md) for production deployment ideas

**Q: Is this legal?**  
A: Yes. It uses only publicly available data via official APIs. See the disclaimer at the top.

---

## License

MIT License — use it, build on it, give credit.
