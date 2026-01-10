import os
from datetime import datetime

import pytest


def test_collector_collects_and_logs(monkeypatch, tmp_path, caplog, app_module):
    main, db = app_module
    # configure collector log file before importing module so it picks up the env
    log_file = tmp_path / "collector.log"
    monkeypatch.setenv("COLLECTOR_LOG_FILE", str(log_file))
    import charon.collector as collector
    import charon.nbp_client as nbp

    FAKE_TABLE = [{"code": "USD", "currency": "US Dollar"}]
    FAKE_HISTORY = [("2024-01-01", 4.0), ("2024-01-02", 4.1)]
    FAKE_GOLD = [("2024-01-01", 250.0)]

    monkeypatch.setattr(nbp, "fetch_table", lambda table="A": FAKE_TABLE)
    monkeypatch.setattr(nbp, "get_recent_currency_history", lambda code, days=60: FAKE_HISTORY)
    monkeypatch.setattr(nbp, "get_recent_gold_history", lambda days=60: FAKE_GOLD)

    caplog.set_level("INFO", logger="charon.collector")

    decisions, fetched_at, history_map = collector.collect(codes=["USD"], days=60)

    # decisions should contain USD and gold
    codes = {d.code for d in decisions}
    assert "USD" in codes
    assert "XAU" in codes

    # history_map should contain both series
    assert "USD" in history_map
    assert "XAU" in history_map

    # DB should have USD and gold rows
    with db.get_session() as session:
        assert session.query(db.Rate).count() >= 2
        assert session.query(db.GoldPrice).count() >= 1

    # caplog should contain informational messages
    assert any("fetched" in rec.getMessage().lower() for rec in caplog.records)
    # log file created
    assert log_file.exists()