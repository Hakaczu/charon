import importlib
import os


def setup_db(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    import charon.db as db

    importlib.reload(db)
    db.init_db()
    return db


def test_save_currency_history_deduplicates(monkeypatch):
    db = setup_db(monkeypatch)

    history1 = [("2024-01-01", 4.0), ("2024-01-02", 4.1)]
    history2 = [("2024-01-02", 4.1), ("2024-01-03", 4.2)]

    with db.get_session() as session:
        inserted1 = db.save_currency_history(session, code="USD", name="Dolar", history=history1)
        inserted2 = db.save_currency_history(session, code="USD", name="Dolar", history=history2)

        assert inserted1 == 2
        assert inserted2 == 1  # jeden rekord duplikat
        assert session.query(db.Rate).count() == 3


def test_save_gold_history_deduplicates(monkeypatch):
    db = setup_db(monkeypatch)

    history = [("2024-01-01", 250.0), ("2024-01-02", 252.0)]
    with db.get_session() as session:
        inserted1 = db.save_gold_history(session, history=history)
        inserted2 = db.save_gold_history(session, history=history)

        assert inserted1 == 2
        assert inserted2 == 0
        assert session.query(db.GoldPrice).count() == 2


def test_latest_rates_order(monkeypatch):
    db = setup_db(monkeypatch)
    history = [("2024-01-01", 4.0), ("2024-01-03", 4.2), ("2024-01-02", 4.1)]
    with db.get_session() as session:
        db.save_currency_history(session, code="USD", name="Dolar", history=history)
        latest = db.latest_rates(session, limit=2)
        assert len(latest) == 2
        assert str(latest[0].effective_date) == "2024-01-03"
        assert str(latest[1].effective_date) == "2024-01-02"


def test_latest_gold_order(monkeypatch):
    db = setup_db(monkeypatch)
    history = [("2024-01-01", 250.0), ("2024-01-03", 260.0), ("2024-01-02", 255.0)]
    with db.get_session() as session:
        db.save_gold_history(session, history=history)
        latest = db.latest_gold(session, limit=2)
        assert len(latest) == 2
        assert str(latest[0].effective_date) == "2024-01-03"
        assert str(latest[1].effective_date) == "2024-01-02"
