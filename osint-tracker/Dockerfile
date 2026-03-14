# ─────────────────────────────────────────────────────────────────
# OSINT Tracker — Multi-Stage Dockerfile
#
# Stage 1 (builder): installs all dependencies into a clean layer
# Stage 2 (runtime): copies only what's needed — lean final image
#
# Result: ~180MB image vs ~600MB single-stage
# ─────────────────────────────────────────────────────────────────

# ── Stage 1: Builder ──────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: Runtime ─────────────────────────────────────────────
FROM python:3.11-slim AS runtime

LABEL maintainer="your@email.com"
LABEL description="OSINT Military Movement Tracker — public open data only"
LABEL version="1.0.0"

ARG BUILD_DATE
ARG GIT_COMMIT
LABEL build-date=$BUILD_DATE
LABEL git-commit=$GIT_COMMIT

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy only app source — no dev files
COPY src/        ./src/
COPY config/     ./config/
COPY tests/      ./tests/
COPY docker/     ./docker/
COPY main.py     .

RUN mkdir -p data/raw data/processed \
    && chmod +x docker/entrypoint.sh

RUN useradd -m -u 1000 -s /bin/bash osintuser \
    && chown -R osintuser:osintuser /app

USER osintuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python main.py --list-regions || exit 1

ENTRYPOINT ["./docker/entrypoint.sh"]
CMD ["--region", "iran", "--days", "7", "--output", "both"]
