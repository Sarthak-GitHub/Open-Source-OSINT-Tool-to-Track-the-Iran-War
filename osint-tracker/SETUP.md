# OSINT Tracker — Complete Setup & Usage Guide

---

## Final Project Structure

```
osint-tracker/
│
├── 📄 main.py                        ← CLI entry point (start here)
├── 📄 requirements.txt               ← Python dependencies
├── 📄 pytest.ini                     ← Test configuration
├── 📄 Makefile                       ← One-command shortcuts
├── 📄 Dockerfile                     ← Multi-stage container build
├── 📄 docker-compose.yml             ← All Docker run profiles
├── 📄 .env.example                   ← API key template (copy → .env)
├── 📄 .gitignore
├── 📄 .dockerignore
├── 📄 README.md
│
├── 📁 src/                           ← All application source code
│   ├── 📁 collectors/                ← Layer 1: fetch public data
│   │   ├── base_collector.py         ← Abstract base + disk cache
│   │   ├── internet_collector.py     ← IODA internet outage API
│   │   ├── conflict_collector.py     ← ACLED armed conflict events
│   │   ├── news_collector.py         ← NewsAPI keyword signals
│   │   └── aircraft_collector.py     ← ADS-B Exchange flight tracker
│   │
│   ├── 📁 analyzers/                 ← Layer 2: process + score signals
│   │   ├── signal_correlator.py      ← Normalise all signals to 0–1
│   │   ├── anomaly_detector.py       ← Threshold-based anomaly flags
│   │   └── pattern_scorer.py         ← Weighted composite score 0–10
│   │
│   └── 📁 visualizers/              ← Layer 3: render output
│       ├── dashboard.py              ← Rich terminal report
│       └── map_renderer.py           ← Folium interactive HTML map
│
├── 📁 config/
│   └── regions.yaml                  ← Regions of interest + thresholds
│
├── 📁 data/                          ← Auto-generated, never committed
│   ├── README.md                     ← Explains raw/processed formats
│   ├── 📁 raw/                       ← Cached API responses (diskcache)
│   │   ├── sample_ioda_iran_*.json   ← What IODA returns
│   │   ├── sample_acled_iran_*.json  ← What ACLED returns
│   │   └── sample_newsapi_iran_*.json← What NewsAPI returns
│   │
│   └── 📁 processed/                 ← Pipeline outputs
│       ├── sample_pipeline_output_*.json  ← Full scored JSON report
│       └── iran_YYYYMMDD_HHMM.html        ← Interactive map (auto-generated)
│
├── 📁 tests/
│   ├── conftest.py                   ← Shared fixtures + load_fixture()
│   ├── test_collectors.py            ← Unit tests for all collectors
│   ├── test_analyzers.py             ← Unit tests for all analyzers
│   ├── test_fixtures.py              ← End-to-end pipeline tests
│   └── 📁 fixtures/                  ← Static mock API responses
│       ├── README.md                 ← How to use fixtures
│       ├── ioda_normal.json          ← Baseline connectivity
│       ├── ioda_outage.json          ← 91% connectivity collapse
│       ├── acled_quiet.json          ← Low conflict activity
│       ├── acled_conflict.json       ← High conflict (12 events)
│       ├── newsapi_baseline.json     ← Normal news volume
│       └── newsapi_spike.json        ← 9x volume spike
│
├── 📁 docker/
│   ├── entrypoint.sh                 ← Smart startup (checks API keys)
│   └── QUICKSTART.md                 ← Docker usage guide
│
├── 📁 scripts/
│   └── run_pipeline.sh               ← Local (non-Docker) runner
│
├── 📁 docs/
│   └── methodology.md                ← OSINT tradecraft explanation
│
└── 📁 .github/
    └── 📁 workflows/
        └── ci.yml                    ← GitHub Actions CI pipeline
```

---

## Option A — Python Virtual Environment

### Step 1: Clone and enter

```bash
git clone https://github.com/yourusername/osint-tracker.git
cd osint-tracker
```

### Step 2: Create virtual environment

```bash
# Create
python3 -m venv venv

# Activate
source venv/bin/activate          # Mac / Linux
venv\Scripts\activate             # Windows
```

You should see `(venv)` in your terminal prompt.

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure API keys

```bash
cp .env.example .env
```

Open `.env` and fill in your keys:

```env
NEWS_API_KEY=your_key_here          # free at newsapi.org
ACLED_API_KEY=your_key_here         # free at acleddata.com
ACLED_EMAIL=your@email.com          # same email you registered with
```

> **No keys?** Leave them blank. The pipeline uses realistic demo
> data automatically. You'll see `[DEMO]` next to those sources.

### Step 5: Run

```bash
# Default — Iran, last 7 days, terminal + HTML map
python main.py

# Custom region and window
python main.py --region israel --days 3
python main.py --region strait_of_hormuz --days 14

# Terminal output only (no HTML)
python main.py --region iran --days 7 --output terminal

# See all available regions
python main.py --list-regions

# Verbose logging for debugging
python main.py --region iran --days 1 --log-level DEBUG
```

### Step 6: View the map

```bash
# Mac
open data/processed/*.html

# Linux
xdg-open data/processed/*.html

# Windows
start data/processed/*.html

# Or just drag the .html file into any browser
```

### Running tests

```bash
# All tests
pytest

# With verbose output
pytest -v

# Specific test file
pytest tests/test_fixtures.py -v

# Only fast unit tests (skip integration)
pytest -m unit
```

### Deactivating the virtual environment

```bash
deactivate
```

---

## Option B — Docker (Recommended for Sharing)

No Python installation needed. Just Docker Desktop.

### Step 1: Clone and configure

```bash
git clone https://github.com/yourusername/osint-tracker.git
cd osint-tracker

# Creates .env from template
make setup
```

Edit `.env` and add your API keys (same as above).

### Step 2: Build the image

```bash
make build
```

Only needed once — or after you change `requirements.txt`.

### Step 3: Run the pipeline

```bash
# Iran, last 7 days (default)
make run

# Custom region / days
make run REGION=israel DAYS=3
make run REGION=strait_of_hormuz DAYS=14

# List all available regions
docker-compose run --rm osint-run --list-regions
```

### Step 4: View the map

```bash
make open-map
# Opens data/processed/iran_YYYYMMDD_HHMM.html in your browser
```

---

## Docker — All Available Commands

```bash
# ── First time ─────────────────────────────────────────────────
make setup            # copy .env.example → .env
make build            # build image (~180MB, multi-stage)

# ── Running ────────────────────────────────────────────────────
make run                            # iran, 7 days
make run REGION=israel DAYS=3       # custom
make run OUTPUT=terminal            # no HTML map

# ── Continuous monitoring ───────────────────────────────────────
make watch                          # re-runs every 6 hours

# ── All regions at once ─────────────────────────────────────────
make all-regions                    # iran + israel + hormuz in parallel

# ── Testing ────────────────────────────────────────────────────
make test                           # run full test suite in Docker

# ── Debugging ──────────────────────────────────────────────────
make shell                          # bash inside the container
make logs                           # tail scheduler logs

# ── Cleanup ────────────────────────────────────────────────────
make clean                          # remove containers + raw cache
make clean-all                      # remove everything including maps
```

---

## Docker Compose — Direct Commands

If you prefer docker-compose directly over `make`:

```bash
# One-off run
docker-compose up osint-run

# Custom args
docker-compose run --rm osint-run --region israel --days 3

# Scheduled (every 6 hours, runs in background)
docker-compose --profile scheduled up -d osint-scheduler
docker-compose --profile scheduled logs -f       # watch logs
docker-compose --profile scheduled down          # stop

# All regions in parallel
docker-compose --profile multi up

# Test suite
docker-compose --profile test run --rm osint-test

# Interactive shell
docker-compose --profile dev run --rm osint-shell
```

---

## What the Output Looks Like

### Terminal Dashboard

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  OSINT TRACKER — IRAN
  Period: 2026-02-21 → 2026-02-28    Generated: 2026-02-28 22:18 UTC
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ╭─ Signal Analysis ────────────────────────────────────────────╮
  │ Layer          Score     Severity    Description              │
  │ ✈ Internet    9.1/10    CRITICAL    91% connectivity loss    │
  │ 📡 Conflict   8.7/10    CRITICAL    40 explosions/battles    │
  │ 📰 News       9.2/10    CRITICAL    News volume 9.2x         │
  │ ✈ Aircraft   8.0/10    HIGH        4 ISR | 12 military      │
  ╰──────────────────────────────────────────────────────────────╯

  ╭─ Overall Assessment ─────────────────────────────────────────╮
  │  Composite Score: 8.9 / 10                                   │
  │  ████████████████████████████████████░░░░░░░                 │
  │  Status: 🔴 HIGH ACTIVITY DETECTED                           │
  ╰──────────────────────────────────────────────────────────────╯

  📍 Conflict Hotspots (ACLED)
    1. Tehran  — 18 events
    2. Isfahan — 9 events
    3. Natanz  — 6 events

  ✈ ISR / Intelligence Aircraft Spotted
    [COBRA11] RC135 — SIGINT/Reconnaissance
    [RIVET22] RC135 — SIGINT/Reconnaissance
    [JAKE11]  KC135 — Air-to-Air Refuelling
    [ODIN41]  E3    — AWACS (airborne surveillance)

  🗺️  Map saved to: data/processed/iran_20260228_2218.html
```

### HTML Map

A self-contained interactive map with:
- Dark `CartoDB` basemap
- Red heatmap showing conflict intensity
- Clickable markers for each conflict event (type, date, notes)
- Aircraft markers for ISR/military flights
- Score legend in bottom-left corner
- Layer controls to toggle on/off

---

## Free API Keys — Where to Get Them

| API | Steps | Time |
|---|---|---|
| **NewsAPI** | Go to newsapi.org → Sign Up → copy key | 2 min |
| **ACLED** | Go to acleddata.com → Request Access → confirm email | 1 day |
| **IODA** | No key needed — public API | 0 min |
| **ADS-B** | No key needed — public feed | 0 min |
| **Sentinel Hub** | sentinel-hub.com → free tier signup | 5 min |

---

## Pipeline Architecture (Quick Reference)

```
Public APIs (IODA, ACLED, NewsAPI, ADS-B)
         │
         ▼
    [Collectors]          ← src/collectors/
    Fetch + Cache         ← 6-hour disk cache (data/raw/)
         │
         ▼
    [Correlator]          ← src/analyzers/signal_correlator.py
    Normalise 0–1         ← same scale across all 4 sources
         │
         ▼
    [Anomaly Detector]    ← src/analyzers/anomaly_detector.py
    Flag + Describe       ← threshold-based, each layer independent
         │
         ▼
    [Pattern Scorer]      ← src/analyzers/pattern_scorer.py
    Weighted 0–10         ← internet 30% | acled 30% | news 20% | aircraft 20%
         │
         ├──▶ Terminal Dashboard   (Rich)
         └──▶ HTML Map             (Folium → data/processed/*.html)
```
