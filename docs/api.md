# Charon API

FastAPI exposes a small read-only API with snapshot data cached in Redis.

Base URL depends on deployment:
- Local dev (compose): `http://localhost:8000`
- With reverse proxy: `/api` is routed to the backend (e.g., `http://localhost/api`)

All endpoints return JSON.

## Endpoints

### `GET /health`
- Purpose: Liveness probe.
- Response: `{ "status": "ok" }`

### `GET /api/v1/snapshot`
- Purpose: Return the full snapshot (decisions + history map + last fetch timestamp).
- Response body:
  ```json
  {
    "items": [
      {
        "name": "dolar amerykański",
        "code": "USD",
        "latest_rate": 4.1234,
        "change_pct": -0.0123,
        "decision": "buy",
        "basis": "1.2% poniżej średniej z 60 dni",
        "icon_class": null
      }
    ],
    "history_map": {
      "USD": [["2024-01-01", 4.2], ["2024-01-02", 4.18]]
    },
    "last_fetch": "2024-01-02T12:00:00Z"
  }
  ```

### `GET /api/v1/rates`
- Purpose: Convenience endpoint with just the `items` array (decisions + last rate).
- Response: same `items` shape as in `/api/v1/snapshot`.

### `GET /api/v1/history?code=USD`
- Purpose: Return historical points for a specific instrument.
- Query params:
  - `code` (required): currency/commodity code, e.g. `USD`, `EUR`, `XAU`.
- Responses:
  - `200 OK`:
    ```json
    {
      "code": "USD",
      "points": [["2024-01-01", 4.2], ["2024-01-02", 4.18]]
    }
    ```
  - `404 Not Found` if the code has no history.

## Error handling
- `404` for unknown codes on `/api/v1/history`.
- Other errors return standard FastAPI error responses.

## Docs & schema
- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`

