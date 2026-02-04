from __future__ import annotations

from typing import List, Tuple


def ema(prices: List[float], span: int) -> List[float]:
    if not prices:
        return []
    alpha = 2 / (span + 1)
    result = [prices[0]]
    for price in prices[1:]:
        result.append(alpha * price + (1 - alpha) * result[-1])
    return result


def macd(prices: List[float], fast: int = 12, slow: int = 26, signal_span: int = 9) -> Tuple[List[float], List[float], List[float]]:
    if len(prices) < slow:
        return [], [], []
    ema_fast = ema(prices, fast)
    ema_slow = ema(prices, slow)
    # Align lengths
    min_len = min(len(ema_fast), len(ema_slow))
    ema_fast = ema_fast[-min_len:]
    ema_slow = ema_slow[-min_len:]
    macd_line = [f - s for f, s in zip(ema_fast, ema_slow)]
    signal_line = ema(macd_line, signal_span)
    hist_len = min(len(macd_line), len(signal_line))
    macd_line = macd_line[-hist_len:]
    signal_line = signal_line[-hist_len:]
    histogram = [m - s for m, s in zip(macd_line, signal_line)]
    return macd_line, signal_line, histogram


def latest_signal(prices: List[float]) -> str:
    macd_line, signal_line, histogram = macd(prices)
    if len(histogram) < 2:
        return "HOLD"
    if histogram[-1] > 0 and histogram[-2] <= 0:
        return "BUY"
    if histogram[-1] < 0 and histogram[-2] >= 0:
        return "SELL"
    return "HOLD"

