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

    def calculate_sma(self, prices: pd.Series, window: int = 50) -> pd.Series:
        """
        Calculates Simple Moving Average (SMA).
        """
        return prices.rolling(window=window).mean()

    def determine_signal(self, current_hist: float, prev_hist: float, rsi: float, current_price: float, sma_val: float) -> str:
        """
        Advanced Confluence Logic:
        1. MACD Crossover (Trigger)
        2. RSI Filter (Condition)
        3. SMA Trend Filter (Context)
        """
        # Basic Triggers
        macd_buy_trigger = prev_hist < 0 and current_hist > 0
        macd_sell_trigger = prev_hist > 0 and current_hist < 0
        
        # Trend Context
        # If SMA is NaN (not enough data), assume neutral (ignore filter) or strict. Let's be safe: assume no trend filter if missing.
        bullish_trend = current_price > sma_val if pd.notna(sma_val) else True
        bearish_trend = current_price < sma_val if pd.notna(sma_val) else True

        # Decision Logic
        if macd_buy_trigger:
            # SCENARIO A: Trend Following Buy
            if bullish_trend and rsi < 70:
                return "BUY"
            # SCENARIO B: Reversal Buy (Oversold bounce even if below SMA)
            if rsi < 30:
                return "BUY"

        if macd_sell_trigger:
            # SCENARIO A: Trend Following Sell
            if bearish_trend and rsi > 30:
                return "SELL"
            # SCENARIO B: Reversal Sell (Overbought dump even if above SMA)
            if rsi > 70:
                return "SELL"
            
        return "HOLD"
