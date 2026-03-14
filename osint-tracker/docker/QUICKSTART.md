# 🐳 Docker Quick-Start Guide

Everything you need to run OSINT Tracker without installing Python, pip, or any dependencies locally. Just Docker.

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Mac/Windows) or Docker Engine (Linux)
- That's it.

---

## Step 1 — Clone and Configure

```bash
git clone https://github.com/yourusername/osint-tracker.git
cd osint-tracker

# Creates .env from the template
make setup
```

Now open `.env` and add your free API keys:

```bash
nano .env   # or code .env, vim .env — whatever you use
```

```env
NEWS_API_KEY=your_newsapi_key_here       # newsapi.org — free
ACLED_API_KEY=your_acled_key_here        # acleddata.com — free academic
ACLED_EMAIL=your_email@example.com
```

> **No keys yet?** The pipeline runs on demo data automatically.  
> You'll see `[DEMO]` next to results. Still fully functional for learning.

---

## Step 2 — Build

```bash
make build
```

This builds a ~180MB multi-stage Docker image. Only needed once
(or after you change `requirements.txt`).

---

## Step 3 — Run

```bash
# Default: Iran, last 7 days
make run

# Custom region and time window
make run REGION=israel DAYS=3
make run REGION=strait_of_hormuz DAYS=14

# See all available regions
docker-compose run --rm osint-run --list-regions
```

**What happens:**
1. Four collectors run in parallel fetching public data
2. Signals are correlated and scored (0–10)
3. A colour-coded terminal report is printed
4. An interactive HTML map is saved to `data/processed/`

---

## Step 4 — View the Map

```bash
make open-map
```

Opens the latest HTML map in your browser. No server needed —
it's a single self-contained file. You can also just:

```bash
open data/processed/*.html        # Mac
xdg-open data/processed/*.html    # Linux
# or drag the file into any browser
```

---

## All Available Commands

```bash
make help           # show all commands
make setup          # first-time: create .env
make build          # build Docker image
make run            # one-off pipeline run
make watch          # run every 6 hours (continuous)
make all-regions    # run all regions in parallel
make test           # run test suite
make shell          # bash inside container (for debugging)
make open-map       # open latest HTML map
make clean          # remove containers + raw cache
make clean-all      # remove everything including outputs
```

---

## Continuous Monitoring

Want it to run automatically every 6 hours and update the map?

```bash
make watch
```

It runs in the foreground. To run in the background:

```bash
docker-compose --profile scheduled up -d osint-scheduler

# Check it's running
docker ps

# See logs
make logs

# Stop it
docker-compose --profile scheduled down
```

---

## Run All Regions in Parallel

```bash
make all-regions
```

This spins up three containers simultaneously — Iran, Israel, and
Strait of Hormuz — each producing its own scored report and HTML map.

Output files will be in `data/processed/`:
```
iran_20260301_0614.html
israel_20260301_0614.html
strait_of_hormuz_20260301_0615.html
```

---

## Debugging Inside the Container

If something isn't working, get a shell inside the container:

```bash
make shell
```

From there you can:
```bash
# Check API keys are loaded
env | grep API

# Run the pipeline manually with debug logging
python main.py --region iran --days 1 --log-level DEBUG

# Run just the tests
pytest tests/ -v

# Check what data was cached
ls data/raw/
```

---

## Common Issues

**"No module named X" error**
```bash
make clean && make build
# The image needs a rebuild after requirements.txt changes
```

**"ACLED returned 403" error**
```bash
# Your ACLED key or email is wrong in .env
# Re-register at acleddata.com — it's free
```

**"0 articles" from NewsAPI**
```bash
# Free tier is limited to 100 requests/day and 30-day history
# Results cached for 6 hours — don't worry about hitting limits
```

**Map file is empty / blank**
```bash
# Usually means no geo_points were returned from ACLED
# Run with demo data: remove ACLED_API_KEY from .env temporarily
```

**Docker build fails on ARM (Apple Silicon)**
```bash
# Add platform flag
docker build --platform linux/amd64 -t osint-tracker .
# Or use: DOCKER_DEFAULT_PLATFORM=linux/amd64 make build
```

---

## Data Privacy

All data processed by this tool is:
- Publicly accessible without authentication (IODA, ADS-B)
- Academic/research-licensed (ACLED)
- Available via free developer tier (NewsAPI)

No personal data is collected or stored.
Raw API responses are cached locally in `data/raw/` only.
Both data directories are in `.gitignore` and never committed.
