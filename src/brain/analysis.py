import pandas as pd
import numpy as np
from typing import Tuple, Optional
from decimal import Decimal

class TechnicalAnalyzer:
    def calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """
        Calculates MACD, Signal Line, and Histogram.
        Returns DataFrame with columns: ['macd', 'signal', 'hist']
        """
        exp1 = prices.ewm(span=fast, adjust=False).mean()
        exp2 = prices.ewm(span=slow, adjust=False).mean()
        
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        
        return pd.DataFrame({
            'macd': macd,
            'signal': signal_line,
            'hist': histogram
        })

    def calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """
        Calculates the Relative Strength Index (RSI).
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def determine_signal(self, current_hist: float, prev_hist: float, rsi: float = 50) -> str:
        """
        Refined signal logic: MACD crossover + RSI Confirmation.
        """
        # Basic MACD Signal
        macd_buy = prev_hist < 0 and current_hist > 0
        macd_sell = prev_hist > 0 and current_hist < 0
        
        # RSI Confirmation (avoid buying when overbought, avoid selling when oversold)
        if macd_buy and rsi < 70:
            return "BUY"
        elif macd_sell and rsi > 30:
            return "SELL"
        else:
            return "HOLD"
