import importlib
from datetime import datetime, timezone

from charon.decision import DecisionResult


class DummyRedis:
    def __init__(self):
        self.data = {}

    def get(self, key):
        return self.data.get(key)

    def setex(self, key, ttl, value):
        self.data[key] = value


def test_run_once_stores_snapshot(monkeypatch):
    import services.miner.main as miner
    importlib.reload(miner)

    fake_redis = DummyRedis()
    monkeypatch.setattr(miner.cache_utils, "get_redis_client", lambda: fake_redis)

    now = datetime.now(timezone.utc)
    decisions = [
        DecisionResult(
            name="US Dollar",
            code="USD",
            latest_rate=4.2,
            change_pct=0.5,
            decision="hold",
            basis="near avg",
        )
    ]
    history_map = {"USD": [("2024-01-01", 4.0), ("2024-01-02", 4.2)]}

    monkeypatch.setattr(
        miner.collector,
        "collect",
        lambda: (decisions, now, history_map),
    )

    miner.run_once()

    assert miner.REDIS_CACHE_KEY in fake_redis.data