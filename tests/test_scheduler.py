import time
from datetime import datetime

import pytest


FAKE_TABLE = [{"code": "USD", "currency": "US Dollar"}]
FAKE_HISTORY = [("2024-01-01", 4.0), ("2024-01-02", 4.1)]
FAKE_GOLD = [("2024-01-01", 250.0)]


def test_refresh_data_populates_cache(monkeypatch, app_module):
    main, _ = app_module

    monkeypatch.setattr(main, "fetch_table", lambda table="A": FAKE_TABLE)
    monkeypatch.setattr(main, "get_recent_currency_history", lambda code, days=60: FAKE_HISTORY)
    monkeypatch.setattr(main, "get_recent_gold_history", lambda days=60: FAKE_GOLD)

    main._CACHE["items"] = []
    main._CACHE["last_fetch"] = None

    main.refresh_data()

    assert main._CACHE["items"]
    assert main._CACHE["last_fetch"] is not None


def test_start_and_stop_scheduler(monkeypatch, app_module):
    main, _ = app_module
    calls = {"n": 0}

    def fake_refresh():
        calls["n"] += 1

    monkeypatch.setattr(main, "refresh_data", fake_refresh)

    sched = main.start_scheduler(interval_seconds=1, run_immediately=True)
    time.sleep(1.2)
    main.stop_scheduler()

    assert calls["n"] >= 1