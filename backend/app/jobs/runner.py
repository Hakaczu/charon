from __future__ import annotations

from app.core.database import SessionLocal
from app.jobs.fetch_rates import run_fetch_job


def main():
    db = SessionLocal()
    try:
        run_fetch_job(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
