from charon.decision import decide_from_history


def test_buy_signal_when_price_below_average():
    history = [(f"2024-01-{i:02d}", 4.0) for i in range(1, 6)] + [("2024-01-06", 3.8)]
    result = decide_from_history(history, bias=1.0)
    assert result.decision == "buy"
    assert result.change_pct < -1


def test_sell_signal_when_price_above_average():
    history = [(f"2024-01-{i:02d}", 4.0) for i in range(1, 6)] + [("2024-01-06", 4.2)]
    result = decide_from_history(history, bias=1.0)
    assert result.decision == "sell"
    assert result.change_pct > 1


def test_hold_when_within_bias():
    history = [(f"2024-01-{i:02d}", 4.0) for i in range(1, 6)] + [("2024-01-06", 4.01)]
    result = decide_from_history(history, bias=1.0)
    assert result.decision == "hold"
    assert abs(result.change_pct) < 1.0


def test_empty_history_raises():
    try:
        decide_from_history([], bias=1.0)
    except ValueError:
        return
    assert False, "ValueError expected for empty history"
