# Multi-stage Dockerfile for API/miner (small runtime, non-root)

FROM python:3.11-slim AS builder
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app

# Install build essentials only if needed (kept minimal here)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create venv and install deps
COPY requirements.txt ./
RUN python -m venv /opt/venv \
  && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# --- Runtime image ---
FROM python:3.11-slim AS runtime
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/opt/venv/bin:$PATH" \
    PORT=8000 \
    DATABASE_URL=sqlite:///charon.db \
    REFRESH_SECONDS=3600
WORKDIR /app

# Copy virtualenv
COPY --from=builder /opt/venv /opt/venv

# Copy only needed app code
COPY charon ./charon
COPY services ./services
COPY requirements.txt ./requirements.txt

# Create non-root user
RUN adduser --disabled-password --gecos "" appuser
USER appuser

EXPOSE 8000

# Default command (overridden by compose for miner)
CMD ["uvicorn", "services.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
