#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# OSINT Tracker — Full Pipeline Runner
#
# Use this for LOCAL (non-Docker) runs.
# For Docker, use: make run   or   docker-compose up osint-run
#
# Usage:
#   ./scripts/run_pipeline.sh                    (iran, 7 days)
#   ./scripts/run_pipeline.sh israel 3           (israel, 3 days)
#   ./scripts/run_pipeline.sh iran 7 terminal    (no HTML map)
# ─────────────────────────────────────────────────────────────────

set -e

REGION=${1:-iran}
DAYS=${2:-7}
OUTPUT=${3:-both}

# ── Colour helpers ─────────────────────────────────────────────────
RED='\033[0;31m'; YELLOW='\033[1;33m'; GREEN='\033[0;32m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

echo ""
echo -e "${CYAN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${CYAN}${BOLD}  🛰️  OSINT Tracker — Local Run${RESET}"
echo -e "${CYAN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "  Region : ${YELLOW}${REGION}${RESET}"
echo -e "  Days   : ${YELLOW}${DAYS}${RESET}"
echo -e "  Output : ${YELLOW}${OUTPUT}${RESET}"
echo ""

# ── Check Python ───────────────────────────────────────────────────
if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
    echo -e "${RED}❌  Python not found. Install Python 3.10+ or use Docker instead.${RESET}"
    echo -e "    Docker: ${CYAN}make run${RESET}"
    exit 1
fi

PYTHON=$(command -v python3 || command -v python)

# ── Activate virtualenv if present ────────────────────────────────
if [ -d "venv" ]; then
    echo -e "  ${GREEN}✓${RESET} Activating virtualenv"
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo -e "  ${GREEN}✓${RESET} Activating .venv"
    source .venv/bin/activate
fi

# ── Check .env ────────────────────────────────────────────────────
if [ ! -f ".env" ]; then
    echo -e "  ${YELLOW}⚠${RESET}  .env not found — running in demo mode"
    echo -e "     Run ${CYAN}make setup${RESET} to configure API keys"
    echo ""
else
    echo -e "  ${GREEN}✓${RESET} .env loaded"
    export $(grep -v '^#' .env | xargs) 2>/dev/null || true
fi

# ── Print data source status ───────────────────────────────────────
echo ""
echo -e "  ${BOLD}Data Source Status:${RESET}"

echo -e "  ${GREEN}✅${RESET}  IODA              — live (no key needed)"

if [ -n "$ACLED_API_KEY" ]; then
    echo -e "  ${GREEN}✅${RESET}  ACLED             — live"
else
    echo -e "  ${YELLOW}⚠️ ${RESET}  ACLED             — demo mode"
fi

if [ -n "$NEWS_API_KEY" ]; then
    echo -e "  ${GREEN}✅${RESET}  NewsAPI           — live"
else
    echo -e "  ${YELLOW}⚠️ ${RESET}  NewsAPI           — demo mode"
fi

echo -e "  ${GREEN}✅${RESET}  ADS-B Exchange    — live (public)"
echo ""

# ── Ensure data dirs exist ────────────────────────────────────────
mkdir -p data/raw data/processed

# ── Run tests first (optional: comment out if slow) ───────────────
echo -e "  ${BOLD}🧪 Running tests...${RESET}"
$PYTHON -m pytest tests/ -q --tb=short 2>&1 | tail -5
echo ""

# ── Run the pipeline ──────────────────────────────────────────────
echo -e "  ${BOLD}📡 Starting pipeline...${RESET}"
echo ""
$PYTHON main.py --region "$REGION" --days "$DAYS" --output "$OUTPUT"
EXIT_CODE=$?

# ── Report outcome ────────────────────────────────────────────────
echo ""
if [ $EXIT_CODE -eq 2 ]; then
    echo -e "${RED}${BOLD}  🔴 HIGH ACTIVITY DETECTED (score ≥ 7.0)${RESET}"
elif [ $EXIT_CODE -eq 1 ]; then
    echo -e "${YELLOW}${BOLD}  🟡 ELEVATED ACTIVITY (score ≥ 4.0)${RESET}"
else
    echo -e "${GREEN}${BOLD}  🟢 Normal activity levels${RESET}"
fi

# ── Show output location ──────────────────────────────────────────
if [ "$OUTPUT" = "html" ] || [ "$OUTPUT" = "both" ]; then
    LATEST=$(ls -t data/processed/*.html 2>/dev/null | head -1)
    if [ -n "$LATEST" ]; then
        echo ""
        echo -e "  🗺️  Map saved: ${CYAN}${LATEST}${RESET}"
        echo -e "     Open with: ${CYAN}make open-map${RESET}"
    fi
fi

echo ""
