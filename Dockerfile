# ════════════════════════════════════════════════════
#  ACEest Fitness – Multi-stage Dockerfile (Flask)
# ════════════════════════════════════════════════════

# ── Stage 1: Builder ────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt


# ── Stage 2: Runtime ────────────────────────────────
FROM python:3.11-slim AS runner

LABEL maintainer="Priya Agarwal"
LABEL version="3.2.4"
LABEL description="ACEest Fitness Flask REST API"

# Non-root security user
RUN groupadd -r aceest && useradd -r -g aceest aceest

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /home/aceest/.local

# Copy application source
COPY app/ ./

# Writable data directory for SQLite
RUN mkdir -p /data && chown -R aceest:aceest /app /data

USER aceest

ENV PATH=/home/aceest/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production
ENV PORT=5000
ENV DB_PATH=/data/aceest_fitness.db

EXPOSE 5000

# Health check: hits Flask /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

CMD ["python", "aceest_app.py"]
