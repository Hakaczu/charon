import datetime as dt
from typing import Dict, List, Tuple

import requests

NBP_BASE_URL = "https://api.nbp.pl/api"
DEFAULT_TIMEOUT = 10

RatePoint = Tuple[str, float]


class NBPError(Exception):
    """Raised when the NBP API returns an unexpected response."""


def _get(url: str) -> requests.Response:
    response = requests.get(url, timeout=DEFAULT_TIMEOUT, headers={"Accept": "application/json"})
    response.raise_for_status()
    return response


def fetch_table(table: str = "A") -> List[Dict]:
    url = f"{NBP_BASE_URL}/exchangerates/tables/{table}?format=json"
    data = _get(url).json()
    if not data:
        raise NBPError("Empty response for currency table")
    return data[0].get("rates", [])


def fetch_currency_history(code: str, start: str, end: str) -> List[RatePoint]:
    url = f"{NBP_BASE_URL}/exchangerates/rates/A/{code}/{start}/{end}?format=json"
    data = _get(url).json()
    rates = data.get("rates", [])
    return [(item["effectiveDate"], float(item["mid"])) for item in rates]


def fetch_gold_history(start: str, end: str) -> List[RatePoint]:
    url = f"{NBP_BASE_URL}/cenyzlota/{start}/{end}?format=json"
    data = _get(url).json()
    return [(item["data"], float(item["cena"])) for item in data]


def recent_date_range(days: int) -> Tuple[str, str]:
    end_date = dt.date.today()
    start_date = end_date - dt.timedelta(days=days)
    return start_date.isoformat(), end_date.isoformat()


def get_recent_currency_history(code: str, days: int = 30) -> List[RatePoint]:
    start, end = recent_date_range(days)
    return fetch_currency_history(code, start, end)


def get_recent_gold_history(days: int = 30) -> List[RatePoint]:
    start, end = recent_date_range(days)
    return fetch_gold_history(start, end)
