import importlib
import sys
from pathlib import Path
from typing import Iterator, Tuple

import pytest

# Ensure project root is on sys.path for module imports
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
importlib.invalidate_caches()


@pytest.fixture()
def app_module(monkeypatch) -> Iterator[Tuple[object, object]]:
    """Reload modules with in-memory DB and return main module and db module."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("REFRESH_SECONDS", "3600")

    import charon.db as db
    import main

    importlib.reload(db)
    importlib.reload(main)

    yield main, db


@pytest.fixture()
def app_client(app_module):
    main, _ = app_module
    return main.app.test_client()
