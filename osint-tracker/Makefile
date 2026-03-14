# ─────────────────────────────────────────────────────────────────────────────
# OSINT Tracker — Makefile
#
# One-command interface for every common operation.
# No need to remember docker-compose flags or Python commands.
#
# Usage:
#   make build          ← build the Docker image
#   make run            ← run pipeline for Iran (default)
#   make run REGION=israel DAYS=3
#   make watch          ← run every 6 hours continuously
#   make all-regions    ← run all regions in parallel
#   make test           ← run test suite inside Docker
#   make shell          ← open bash inside the container
#   make clean          ← remove containers and cache
# ─────────────────────────────────────────────────────────────────────────────

# ── Config ────────────────────────────────────────────────────────────────────
REGION   ?= iran
DAYS     ?= 7
OUTPUT   ?= both
IMAGE    := osint-tracker
COMPOSE  := docker-compose

# Build metadata
BUILD_DATE  := $(shell date -u +%Y-%m-%dT%H:%M:%SZ)
GIT_COMMIT  := $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")

.PHONY: help build run watch all-regions test shell clean logs open-map setup

# ── Default target: show help ─────────────────────────────────────────────────
help:
	@echo ""
	@echo "  🛰️  OSINT Tracker — Available Commands"
	@echo "  ────────────────────────────────────────────────────────"
	@echo "  make setup           Copy .env.example → .env (first time)"
	@echo "  make build           Build Docker image"
	@echo "  make run             Run pipeline (default: iran, 7 days)"
	@echo "  make run REGION=israel DAYS=3"
	@echo "  make watch           Run every 6 hours continuously"
	@echo "  make all-regions     Run iran + israel + hormuz in parallel"
	@echo "  make test            Run test suite inside Docker"
	@echo "  make shell           Open interactive bash in container"
	@echo "  make open-map        Open latest HTML map in browser"
	@echo "  make logs            Tail scheduler logs"
	@echo "  make clean           Stop containers, remove cache"
	@echo "  ────────────────────────────────────────────────────────"
	@echo ""

# ── First-time setup ──────────────────────────────────────────────────────────
setup:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✅  .env created — edit it and add your API keys"; \
		echo "    Required: NEWS_API_KEY, ACLED_API_KEY, ACLED_EMAIL"; \
		echo "    Optional: SENTINEL_CLIENT_ID, SENTINEL_CLIENT_SECRET"; \
	else \
		echo "⚠️   .env already exists — not overwriting"; \
	fi
	@mkdir -p data/raw data/processed

# ── Build ─────────────────────────────────────────────────────────────────────
build:
	@echo "🔨 Building Docker image..."
	$(COMPOSE) build \
		--build-arg BUILD_DATE=$(BUILD_DATE) \
		--build-arg GIT_COMMIT=$(GIT_COMMIT)
	@echo "✅  Image built: $(IMAGE)"

# ── One-off pipeline run ──────────────────────────────────────────────────────
run: _check_env
	@echo "🛰️  Running OSINT pipeline — Region: $(REGION) | Days: $(DAYS)"
	$(COMPOSE) run --rm osint-run \
		--region $(REGION) \
		--days $(DAYS) \
		--output $(OUTPUT)

# ── Continuous scheduler (every 6 hours) ─────────────────────────────────────
watch: _check_env
	@echo "⏱️  Starting scheduler — runs every 6 hours"
	@echo "   Press Ctrl+C to stop"
	$(COMPOSE) --profile scheduled up osint-scheduler

# ── All regions in parallel ───────────────────────────────────────────────────
all-regions: _check_env
	@echo "🌍 Running all regions in parallel..."
	$(COMPOSE) --profile multi up

# ── Test suite ────────────────────────────────────────────────────────────────
test:
	@echo "🧪 Running test suite..."
	$(COMPOSE) --profile test run --rm osint-test
	@echo "✅  Tests complete"

# ── Interactive shell ─────────────────────────────────────────────────────────
shell:
	@echo "🐚 Opening shell inside container..."
	$(COMPOSE) --profile dev run --rm osint-shell

# ── Open latest HTML map in browser ──────────────────────────────────────────
open-map:
	@LATEST=$$(ls -t data/processed/*.html 2>/dev/null | head -1); \
	if [ -z "$$LATEST" ]; then \
		echo "❌  No HTML maps found in data/processed/ — run 'make run' first"; \
	else \
		echo "🗺️  Opening: $$LATEST"; \
		if command -v xdg-open > /dev/null; then xdg-open "$$LATEST"; \
		elif command -v open > /dev/null; then open "$$LATEST"; \
		else echo "   File is at: $$LATEST"; fi; \
	fi

# ── Tail scheduler logs ───────────────────────────────────────────────────────
logs:
	$(COMPOSE) logs -f osint-scheduler

# ── Clean up ──────────────────────────────────────────────────────────────────
clean:
	@echo "🧹 Cleaning up containers and cache..."
	$(COMPOSE) down --remove-orphans 2>/dev/null || true
	docker rmi $(IMAGE) 2>/dev/null || true
	rm -rf data/raw/
	@echo "✅  Cleaned (processed outputs kept in data/processed/)"

clean-all: clean
	rm -rf data/processed/
	@echo "✅  All data cleared"

# ── Internal: check .env exists before running ───────────────────────────────
_check_env:
	@if [ ! -f .env ]; then \
		echo "❌  .env file not found. Run: make setup"; \
		exit 1; \
	fi
