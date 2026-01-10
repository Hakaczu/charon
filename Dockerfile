# Dockerfile for Charon
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

# System deps (minimal) and cleanup
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (leverage layer cache)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 8000

# Default envs (can be overridden at runtime)
ENV PORT=8000 \
    DATABASE_URL=sqlite:///charon.db \
    REFRESH_SECONDS=3600

# Run FastAPI (api service). docker-compose overrides the command as needed.
CMD ["uvicorn", "services.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
