from app.services.signal_engine import calculate_signal


def test_calculate_signal_buy():
    mids = [1.0 + 0.001 * i for i in range(30)]
    mids[-1] = 0.9
    result = calculate_signal(mids, bid=0.89, ask=0.91)
    assert result.signal in {"BUY", "HOLD"}
    assert result.confidence <= 1.0


def test_calculate_signal_insufficient():
    result = calculate_signal([1.0] * 10, bid=None, ask=None)
    assert result.signal == "HOLD"
    assert result.confidence == 0.3
