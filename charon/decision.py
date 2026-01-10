from dataclasses import dataclass
from statistics import mean
from typing import List, Optional

from .nbp_client import RatePoint


@dataclass
class DecisionResult:
    name: str
    code: str
    latest_rate: float
    change_pct: Optional[float]
    decision: str
    basis: str


def _percent_change(current: float, reference: float) -> Optional[float]:
    if reference == 0:
        return None
    return (current - reference) / reference * 100


def decide_from_history(history: List[RatePoint], bias: float = 1.0) -> DecisionResult:
    """
    Given rate history for a single instrument (currency or gold), return a decision.

    Heuristic: compare latest rate to the moving average. If latest is higher than
    average by >bias%, signal "sell"; if lower by >bias%, signal "buy"; otherwise "hold".
    """
    if not history:
        raise ValueError("History is empty; cannot decide")

    dates, values = zip(*history)
    latest_rate = float(values[-1])
    avg_rate = mean(values)
    change_pct = _percent_change(latest_rate, avg_rate)

    if change_pct is None:
        decision = "hold"
        basis = "Brak zmian referencyjnych"
    elif change_pct > bias:
        decision = "sell"
        basis = f"{change_pct:.2f}% powyżej średniej ({avg_rate:.4f})"
    elif change_pct < -bias:
        decision = "buy"
        basis = f"{change_pct:.2f}% poniżej średniej ({avg_rate:.4f})"
    else:
        decision = "hold"
        basis = f"W pobliżu średniej ({avg_rate:.4f})"

    return DecisionResult(
        name="",
        code="",
        latest_rate=latest_rate,
        change_pct=change_pct,
        decision=decision,
        basis=basis,
    )
