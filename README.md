# Charon FX

Charon FX is a production-ready MVP that fetches daily NBP exchange rates, stores history, and computes simple BUY/SELL/HOLD signals.

## Architecture
- **Backend**: FastAPI + SQLAlchemy + Alembic (Python 3.12)
- **Database**: PostgreSQL 16
- **Worker**: Cron-driven job container for daily fetches
- **Frontend**: Next.js + Tailwind

## Services
- `backend`: REST API
- `worker`: scheduled fetch job
- `frontend`: dashboard UI
- `db`: PostgreSQL

## Setup
1. Copy environment configuration:

```bash
cp .env.example .env
```

2. Start services:

```bash
make dev-up
```

3. Run migrations:

```bash
make migrate
```

4. Trigger a fetch job manually:

```bash
make job
```

## API
- `GET /api/status`
- `GET /api/instruments`
- `GET /api/quotes/latest?codes=USD,EUR`
- `GET /api/quotes/{code}/history?days=90`
- `GET /api/signals/latest?codes=USD,EUR`
- `POST /api/admin/run-fetch` (use `X-Admin-Token`)

## Tests

```bash
make test
```

## Notes
- Uses UTC timestamps in DB; API responses include Warsaw time.
- Silver provider is disabled by default; replace with an external provider as needed.
