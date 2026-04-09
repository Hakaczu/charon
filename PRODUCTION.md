# Charon — Production Deployment Guide

This guide explains how to run the full Charon stack on a production server using
pre-built Docker images published to the **GitHub Container Registry (GHCR)**.

> **Prerequisites**: Docker ≥ 24 and Docker Compose plugin v2 installed on the host.
> No source code is needed — all images are pulled from GHCR.

---

## 1. Pull the compose file

Download just the two files you need:

```bash
curl -fsSL https://raw.githubusercontent.com/Hakaczu/charon/main/docker-compose.prod.yml \
     -o docker-compose.prod.yml

curl -fsSL https://raw.githubusercontent.com/Hakaczu/charon/main/.env.prod.example \
     -o .env.prod.example
```

Or clone the repository and use the files from it:

```bash
git clone https://github.com/Hakaczu/charon.git
cd charon
```

---

## 2. Configure environment variables

```bash
cp .env.prod.example .env.prod
```

Open `.env.prod` in your editor and **change at minimum**:

| Variable | What to set |
|----------|-------------|
| `POSTGRES_PASSWORD` | A strong, unique password |
| `POSTGRES_USER` | Postgres username (default: `charon`) |
| `POSTGRES_DB` | Database name (default: `charon_db`) |
| `TZ` | Your server timezone (e.g. `Europe/Warsaw`) |

All other variables have sensible defaults and can be left as-is for a standard
deployment.

> `.env.prod` is listed in `.gitignore` and must **never** be committed.

---

## 3. Authenticate with GHCR (first time only)

The images are stored in the GitHub Container Registry. If they are public you
can skip this step. For private packages, authenticate with a
[Personal Access Token](https://github.com/settings/tokens) that has
`read:packages` scope:

```bash
echo "$GITHUB_TOKEN" | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
```

---

## 4. Pull and start the stack

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod pull
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

Docker will start six containers in the correct dependency order:

| Container | Role | Default port |
|-----------|------|-------------|
| `db` | PostgreSQL 15 | internal only |
| `redis` | Redis 7 | internal only |
| `miner` | NBP data ingestion (hourly) | — |
| `brain` | MACD signal calculation | — |
| `api` | FastAPI REST API | `8000` |
| `frontend` | Streamlit dashboard | `8501` |

---

## 5. Verify the deployment

```bash
# All containers should be "Up" (healthy for db/redis)
docker compose -f docker-compose.prod.yml ps

# API health endpoint
curl http://localhost:8000/health

# Miner job status
curl http://localhost:8000/stats/miner
```

Open `http://<your-server-ip>:8501` in a browser to see the Streamlit dashboard.

---

## 6. Updating to a new version

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod pull
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

Docker Compose replaces only the containers whose image digest has changed.

---

## 7. Viewing logs

```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Single service
docker compose -f docker-compose.prod.yml logs -f miner
docker compose -f docker-compose.prod.yml logs -f brain
```

Log rotation is configured automatically (max 10 MB × 3 files per container).

---

## 8. Stopping the stack

```bash
# Stop but keep data volumes
docker compose -f docker-compose.prod.yml down

# Stop AND remove all data (destructive!)
docker compose -f docker-compose.prod.yml down -v
```

---

## 9. Exposing services publicly (optional)

By default only ports **8000** (API) and **8501** (frontend) are bound to the
host. For production it is strongly recommended to put a reverse proxy
(e.g. **nginx** or **Caddy**) in front with HTTPS:

```nginx
# nginx example snippet
server {
    listen 443 ssl;
    server_name charon.example.com;

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
    }

    location / {
        proxy_pass http://127.0.0.1:8501/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 10. Data persistence

| Volume | Contents |
|--------|---------|
| `postgres_data` | All rates, signals, and job history |
| `redis_data` | Redis RDB snapshot (optional, survives restarts) |

Both volumes are managed by Docker and survive container restarts and upgrades.
Back them up with your preferred volume backup tool or `pg_dump`.

---

## Architecture overview

```
┌─────────────┐     HTTP      ┌─────────────┐
│  Browser    │──────────────▶│  frontend   │ :8501
└─────────────┘               └──────┬──────┘
                                     │ HTTP
                               ┌─────▼──────┐
                               │    api      │ :8000
                               └──┬──────┬──┘
                                  │      │
                        ┌─────────▼─┐ ┌──▼──────┐
                        │ PostgreSQL│ │  Redis  │
                        └─────┬─────┘ └──┬──────┘
                              │           │ Pub/Sub
                        ┌─────▼──────┐ ┌──▼──────┐
                        │   miner    │ │  brain  │
                        └────────────┘ └─────────┘
```

`miner` fetches NBP exchange rates and gold prices every hour, writes them to
PostgreSQL, and publishes an event on Redis. `brain` receives the event and
computes EMA/MACD trading signals, which `api` then serves to `frontend`.
