import importlib
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure project root is on sys.path for module imports
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
importlib.invalidate_caches()


class DummyRedis:
    def __init__(self):
        self.storage = {}

    def get(self, key):
        return self.storage.get(key)

    def setex(self, key, ttl, value):
        self.storage[key] = value


@pytest.fixture()
def db_module(monkeypatch):
    """In-memory DB for tests."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    import charon.db as db

    importlib.reload(db)
    db.init_db()
    return db


@pytest.fixture()
def api_client(monkeypatch, db_module):
    """FastAPI test client with fake Redis snapshot store."""
    import services.api.main as api

    importlib.reload(api)
    fake_redis = DummyRedis()
    monkeypatch.setattr(api.cache_utils, "get_redis_client", lambda: fake_redis)
    client = TestClient(api.app)
    return client, fake_redis, api
