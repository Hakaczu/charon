from __future__ import annotations

from datetime import datetime

from croniter import croniter
from zoneinfo import ZoneInfo


def next_run(cron_expr: str, tz_name: str, base_time: datetime | None = None) -> datetime:
    tz = ZoneInfo(tz_name)
    base = base_time.astimezone(tz) if base_time else datetime.now(tz)
    return croniter(cron_expr, base).get_next(datetime)
