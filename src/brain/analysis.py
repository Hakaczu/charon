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

    def determine_signal(self, current_hist: float, prev_hist: float) -> str:
        """
        Simple MACD crossover strategy on Histogram.
        """
        if prev_hist < 0 and current_hist > 0:
            return "BUY"
        elif prev_hist > 0 and current_hist < 0:
            return "SELL"
        else:
            return "HOLD"
