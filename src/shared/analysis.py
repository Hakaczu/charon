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

    def calculate_bollinger_bands(self, prices: pd.Series, window: int = 20, num_std: float = 2.0) -> pd.DataFrame:
        """
        Calculates Bollinger Bands.
        Returns DataFrame with 'bb_upper', 'bb_mid', 'bb_lower'.
        """
        sma = prices.rolling(window=window).mean()
        std = prices.rolling(window=window).std()
        upper = sma + (std * num_std)
        lower = sma - (std * num_std)
        return pd.DataFrame({
            'bb_upper': upper,
            'bb_mid': sma,
            'bb_lower': lower
        })

    def determine_signal(self, current_hist: float, prev_hist: float, rsi: float, current_price: float, sma_val: float, bb_lower: float = None, bb_upper: float = None) -> str:
        """
        Advanced Confluence Logic:
        1. MACD Crossover (Trigger)
        2. RSI Filter (Condition)
        3. SMA Trend Filter (Context)
        4. Bollinger Bands (Extreme Volatility Reversal)
        """
        # Basic Triggers
        macd_buy_trigger = prev_hist < 0 and current_hist > 0
        macd_sell_trigger = prev_hist > 0 and current_hist < 0
        
        # Trend Context
        bullish_trend = current_price > sma_val if pd.notna(sma_val) else True
        bearish_trend = current_price < sma_val if pd.notna(sma_val) else True
        
        # BB Context (if provided)
        # Price below lower band = potential oversold reversal
        # Price above upper band = potential overbought reversal
        below_bb = current_price < bb_lower if bb_lower is not None and pd.notna(bb_lower) else False
        above_bb = current_price > bb_upper if bb_upper is not None and pd.notna(bb_upper) else False

        # Decision Logic
        if macd_buy_trigger:
            # SCENARIO A: Trend Following Buy
            if bullish_trend and rsi < 70:
                return "BUY"
            # SCENARIO B: Reversal Buy (Oversold RSI or Below BB)
            if rsi < 30 or below_bb:
                return "BUY"

        if macd_sell_trigger:
            # SCENARIO A: Trend Following Sell
            if bearish_trend and rsi > 30:
                return "SELL"
            # SCENARIO B: Reversal Sell (Overbought RSI or Above BB)
            if rsi > 70 or above_bb:
                return "SELL"
            
        return "HOLD"
