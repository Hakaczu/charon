from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, pstdev
from typing import Iterable


@dataclass
class SignalResult:
    signal: str
    confidence: float
    score: float
    summary: str
    explain: dict


MODEL_VERSION = "v1"


def calculate_signal(mid_series: Iterable[float], bid: float | None, ask: float | None) -> SignalResult:
    values = [value for value in mid_series if value is not None]
    if len(values) < 30:
        return SignalResult(
            signal="HOLD",
            confidence=0.3,
            score=0.0,
            summary="Not enough data for signal.",
            explain={"reason": "insufficient_data", "count": len(values)},
        )

    window30 = values[-30:]
    window7 = values[-7:]
    sma30 = mean(window30)
    sma7 = mean(window7)
    std30 = pstdev(window30)
    std30 = std30 if std30 > 0 else 1e-9
    z_score = (values[-1] - sma30) / std30

    slope_points = window7[-3:]
    slope = slope_points[-1] - slope_points[0]

    spread_ratio = None
    if bid is not None and ask is not None and values[-1] != 0:
        spread_ratio = (ask - bid) / values[-1]

    signal = "HOLD"
    reason = "Neutral conditions"
    if z_score < -0.8 and slope > 0:
        signal = "BUY"
        reason = "Mean reversion signal with rising SMA7"
    elif z_score > 0.8 and slope < 0:
        signal = "SELL"
        reason = "Mean reversion signal with falling SMA7"

    confidence = 1.0
    if spread_ratio is not None and spread_ratio > 0.008:
        confidence *= 0.7
    if std30 < 0.0001:
        confidence *= 0.6

    summary = f"{signal}: {reason}. z={z_score:.2f}"

    return SignalResult(
        signal=signal,
        confidence=round(confidence, 4),
        score=z_score,
        summary=summary,
        explain={
            "sma7": sma7,
            "sma30": sma30,
            "std30": std30,
            "z": z_score,
            "sma7_slope": slope,
            "spread_ratio": spread_ratio,
            "reason": reason,
        },
    )
