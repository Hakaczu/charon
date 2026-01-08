from __future__ import annotations

from datetime import date
from typing import Protocol


class SilverProvider(Protocol):
    def enabled(self) -> bool:  # pragma: no cover - interface
        ...

    def latest_price(self) -> tuple[date, float]:  # pragma: no cover - interface
        ...


class DisabledSilverProvider:
    def enabled(self) -> bool:
        return False

    def latest_price(self) -> tuple[date, float]:
        raise NotImplementedError("Silver provider is disabled")
