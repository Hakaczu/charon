import importlib
from typing import List, Tuple

import pytest


FAKE_TABLE = [
    {"code": code, "currency": f"Name {code}"}
    for code in ["USD", "EUR", "JPY", "GBP", "AUD", "CAD", "CHF", "CNY", "SEK", "NZD", "NOK"]
]
FAKE_HISTORY: List[Tuple[str, float]] = [
    ("2024-01-01", 4.0),
    ("2024-01-02", 4.1),
]
FAKE_GOLD: List[Tuple[str, float]] = [
    ("2024-01-01", 250.0),
    ("2024-01-02", 255.0),
]


@pytest.fixture()
def fake_data(monkeypatch, app_module):
    main, _ = app_module

    def fake_fetch_table(table: str = "A"):
        return FAKE_TABLE

    def fake_history(code: str, days: int = 60):
        return FAKE_HISTORY

    def fake_gold(days: int = 60):
        return FAKE_GOLD

    import charon.nbp_client as nbp

    monkeypatch.setattr(nbp, "fetch_table", fake_fetch_table)
    monkeypatch.setattr(nbp, "get_recent_currency_history", fake_history)
    monkeypatch.setattr(nbp, "get_recent_gold_history", fake_gold)
    # reset cache
    main._CACHE["items"] = []
    main._CACHE["last_fetch"] = None
    main._CACHE["history_map"] = {}
    # prepopulate cache via refresh (no fetch during request)
    main.refresh_data()
    return main


def test_health(app_client):
    resp = app_client.get("/health")
    assert resp.status_code == 200
    assert resp.json == {"status": "ok"}


def test_index_renders(fake_data):
    main = fake_data
    client = main.app.test_client()
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.data.decode()
    # Should include at least one currency code from fake data
    assert "USD" in body
    assert "Ostatnie pobranie" in body
