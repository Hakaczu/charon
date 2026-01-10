# Charon

Charon fetches current and historical FX rates from the Polish NBP (table A) and gold prices (`/cenyzlota`). It compares the latest rate to the recent average to produce a **buy / sell / hold** signal. The backend is FastAPI plus a separate miner that writes a snapshot to Redis; the frontend is a Next.js app.

## Requirements

- Python 3.10+
- Internet access (NBP API)

## Installation (backend)

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Local run (backend)

FastAPI API:

```bash
uvicorn services.api.main:app --host 0.0.0.0 --port 8000
```

Miner (periodically fetches data and writes a snapshot to Redis):

```bash
python -m services.miner.main
```

### Frontend (Next.js)

The Next.js app lives in `frontend/`. By default it talks to FastAPI on port `8000`.

```bash
# 1) Start the API
uvicorn services.api.main:app --host 0.0.0.0 --port 8000

# 2) Start the frontend
cd frontend
cp .env.local.example .env.local   # optional, set API address
npm install
npm run dev  # http://localhost:3000
```

Frontend env (`frontend/.env.local`):
- `NEXT_PUBLIC_API_BASE` — FastAPI address (e.g., `http://localhost:8000`).
- `NEXT_PUBLIC_REFRESH_SECONDS` — optional refresh cadence used for the next-refresh hint.

### Docker / docker-compose (dev stack: backend + frontend)

```bash
docker-compose up
```

- FastAPI backend: `http://127.0.0.1:8000/`
- Next.js frontend: `http://127.0.0.1:3000/`
- Postgres (`db`) is used by default; credentials are in `docker-compose.yml`.
- On first start, `docker/init-db.sql` creates the `charon` role and database.
- App and collector logs are stored in the `app_logs` volume (mounted to `/app/logs` inside the container).
- You can override env vars (`REFRESH_SECONDS`, `SCHEDULER_ENABLED`, `DATABASE_URL`, `LOG_FILE`, `COLLECTOR_LOG_FILE`, etc.) via `docker-compose.yml` or a `.env` file.
- If you previously created a `db_data` volume without the `charon` user, remove it: `docker volume rm charon_db_data`.

The frontend respects `NEXT_PUBLIC_API_BASE` and `NEXT_PUBLIC_REFRESH_SECONDS` set in compose (default `http://api:8000`).

Published container images (GHCR):

- `ghcr.io/hakaczu/charon-api`
- `ghcr.io/hakaczu/charon-miner`
- `ghcr.io/hakaczu/charon-frontend`

If the registry is private, log in first:

```bash
echo "$GITHUB_TOKEN" | docker login ghcr.io -u <your-github-username> --password-stdin
```

### Production mode with reverse proxy (Nginx, ports 80/443)

Run the full stack with Nginx proxying `/api` to the backend and everything else to the frontend using `docker-compose.prod.yml`:

```bash
docker-compose -f docker-compose.prod.yml up
```

- Nginx listens on `80` and `443` and routes `/api` to `api:8000`, all other traffic to `frontend:3000`.
- The frontend is configured with `NEXT_PUBLIC_API_BASE=/api`, so all requests go through the proxy.
- TLS is **not** provided by default (port 443 is exposed without certs). Add your own certificates in `docker/reverse-proxy.conf` if needed.

### API docs

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`
- Markdown summary: `docs/api.md`

### .env configuration

Copy `.env.example` to `.env` and adjust (for backend/miner):
- `PORT=8000`
- `DATABASE_URL=sqlite:///charon.db` (local) or e.g. `postgresql+psycopg2://user:pass@localhost/dbname`
- `REFRESH_SECONDS=3600` (how often the miner refreshes NBP data)
- `REDIS_URL=redis://localhost:6379/0`, `REDIS_CACHE_KEY=charon:cache`
- `COLLECTOR_LOG_FILE=collector.log` (collector log path)

`.env` is git-ignored; you can also override via environment variables at runtime. `python-dotenv` loads `.env` automatically on start.

### Database

- SQLite (`charon.db` in the project root) is the default.
- Point `DATABASE_URL` to another engine (PostgreSQL/MySQL compatible with SQLAlchemy) if you prefer.
- Tables are initialized automatically at app startup.

## Tests

```bash
pytest
```

### Linting & formatting

```bash
ruff check .
black .
mypy .
```

## How it works

- `charon/nbp_client.py` — fetches current and historical FX + gold from the NBP API.
- `charon/decision.py` — compares the latest rate to the recent average; default threshold ±1%.
- `charon/db.py` — SQLAlchemy models and history persistence (default SQLite).
- `services/api/main.py` — FastAPI exposing the snapshot and history from Redis.
- `services/miner/main.py` — periodic collector writing the snapshot to Redis.

Configurable parameters (in `main.py` or via `.env`):
- `HISTORY_DAYS` — how many days of history to consider (default 60).
- `DECISION_BIAS_PERCENT` — threshold for buy/sell signal (default 1%).
- `REFRESH_SECONDS` — refresh cadence (default 3600s); the frontend shows last/next refresh.
- Currency set is fixed (top 10) and gold is always included.
- `LOG_FILE` — log path (default `charon.log`, rotation 1 MB, 3 backups).
- Collector logs: `collector.log` (configurable via `COLLECTOR_LOG_FILE`).
- Cache: `REDIS_URL`, `REDIS_ENABLED` — when enabled, snapshots (items + history) are stored in Redis; views read from the cached snapshot instead of hitting NBP per request.

## Notes

- `/health` returns a simple JSON for monitoring.
- `db/charon.sql` contains a MySQL schema sketch for persistence if needed, but the app runs without it.
