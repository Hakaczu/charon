from __future__ import annotations

import datetime as dt
import logging
from typing import Dict, List

import httpx

from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class NBPClient:
    def __init__(self) -> None:
        self.base_url = settings.nbp_base_url.rstrip("/")
        self.client = httpx.AsyncClient(base_url=self.base_url, headers={"Accept": "application/json"})

    async def fetch_rates(self, start: dt.date, end: dt.date) -> List[Dict]:
        # NBP limit ~93 days per query
        path = f"/api/exchangerates/tables/A/{start}/{end}"
        resp = await self.client.get(path)
        resp.raise_for_status()
        data = resp.json()
        return data

    async def fetch_gold(self, start: dt.date, end: dt.date) -> List[Dict]:
        path = f"/api/cenyzlota/{start}/{end}"
        resp = await self.client.get(path)
        resp.raise_for_status()
        return resp.json()

    async def close(self) -> None:
        await self.client.aclose()

