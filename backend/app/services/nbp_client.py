from __future__ import annotations

from datetime import date
from typing import Any

import httpx


class NbpClient:
    def __init__(self, base_url: str = "https://api.nbp.pl") -> None:
        self.base_url = base_url

    def _get(self, path: str) -> Any:
        url = f"{self.base_url}{path}"
        response = httpx.get(url, timeout=20.0)
        response.raise_for_status()
        return response.json()

    def fetch_table_a(self) -> list[dict[str, Any]]:
        return self._get("/api/exchangerates/tables/A?format=json")

    def fetch_table_c(self) -> list[dict[str, Any]]:
        return self._get("/api/exchangerates/tables/C?format=json")

    def fetch_gold(self) -> list[dict[str, Any]]:
        return self._get("/api/cenyzlota?format=json")

    def fetch_with_fallback(self, fetcher):
        try:
            return fetcher()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code != 404:
                raise
        return fetcher()


def parse_effective_date(payload: list[dict[str, Any]]) -> date:
    entry = payload[0]
    return date.fromisoformat(entry.get("effectiveDate") or entry.get("data"))
