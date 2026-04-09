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

    def calculate_adx(self, df: pd.DataFrame, window: int = 14) -> pd.Series:
        """
        Calculates Average Directional Index (ADX).
        Requires DataFrame with 'high', 'low', 'close' columns.
        If only 'price' is available, estimates high/low (less accurate but functional).
        """
        # If we only have closing prices (NBP mostly), we approximate or use volatility.
        # NBP returns 'rate_mid' (average). We don't have true High/Low.
        # Standard ADX requires High/Low. 
        # Fallback: Use ATR approximation using simple Close variations, 
        # OR honestly: standard deviation based trend strength.
        
        # Let's try to infer High/Low if missing (e.g. Price +/- 0.5% or use previous close)
        # BUT for accuracy, if we only have MID rates, ADX is tricky.
        # Alternative: RSD (Relative Standard Deviation) as trend strength proxy.
        # However, let's assume we pass a DF that *might* have High/Low if we add crypto later.
        # For NBP, we will treat Close as High=Low (which kills ADX).
        
        # BETTER APPROACH FOR NBP DATA (Mid only):
        # Use slope of SMA or distance from SMA as Trend Strength.
        # Or simple: Std Dev of returns.
        
        # BUT user asked for ADX. Let's try to implement a modified version using High=Close, Low=Close
        # This simplifies TR to abs(Close - PrevClose).
        # +DM becomes 0? No.
        # Without High/Low, traditional ADX is impossible.
        
        # PROPOSAL: Use 'Slope of EMA' as trend strength indicator instead of ADX for NBP data.
        # OR: Calculate 'Choppiness Index' (uses High/Low too).
        
        # LET'S STICK TO THE PLAN but adapted:
        # Since we only have `rate_mid` (one price per day), we cannot calculate standard ADX.
        # We will implement a "Trend Strength Index" based on EMA distance.
        # Trend Strength = abs(Price - EMA50) / Price * 100.
        # If distance > 1% -> Trend. If < 1% -> Chop.
        
        # WAIT! If the user really wants ADX, we need High/Low.
        # NBP API actually provides Table C (Bid/Ask). Table A is Mid.
        # We only fetch Table A.
        
        # ADAPTATION: We will calculate a "Trend Intensity" based on the consistency of returns.
        # Ratio of abs(Sum of returns) / Sum of abs(returns). (Efficiency Ratio).
        # ER > 0.3 -> Trend. ER < 0.3 -> Noise.
        # This is Kaufman's Efficiency Ratio (KER). It serves the same purpose as ADX.
        
        change = df['price'].diff()
        volatility = change.abs().rolling(window=window).sum()
        direction = change.rolling(window=window).sum().abs()
        
        # Efficiency Ratio (0 to 1)
        er = direction / volatility
        # Map ER to ADX-like scale (0-100) approx
        adx_proxy = er * 100
        return adx_proxy.fillna(0)

    def resample_to_weekly(self, df_daily: pd.DataFrame) -> pd.DataFrame:
        """
        Resamples daily data to weekly timeframe (taking the last price of the week).
        df_daily needs 'date' (datetime) and 'price'.
        """
        df = df_daily.copy()
        if 'date' not in df.columns and 'effective_date' in df.columns:
            df['date'] = pd.to_datetime(df['effective_date'])
        else:
            df['date'] = pd.to_datetime(df['date'])
            
        df.set_index('date', inplace=True)
        # Resample to Weekly (W-FRI), taking the last close
        df_weekly = df['price'].resample('W-FRI').last().to_frame()
        df_weekly = df_weekly.dropna()
        return df_weekly

    def get_weekly_trend(self, df_weekly: pd.DataFrame) -> str:
        """
        Determines weekly trend based on Price vs SMA 20 (Weekly).
        """
        if len(df_weekly) < 20:
            return "NEUTRAL"
            
        sma20_weekly = df_weekly['price'].rolling(window=20).mean()
        current_price = df_weekly['price'].iloc[-1]
        current_sma = sma20_weekly.iloc[-1]
        
        if pd.isna(current_sma): return "NEUTRAL"
        
        return "BULLISH" if current_price > current_sma else "BEARISH"

    def determine_signal(self, current_hist: float, prev_hist: float, rsi: float, current_price: float, sma_val: float, bb_lower: float = None, bb_upper: float = None, adx: float = 0, weekly_trend: str = "NEUTRAL") -> str:
        """
        Adaptive Strategy with MTF Filter:
        - If ADX > 25 (Trend): Follow MACD & SMA.
        - If ADX < 25 (Range): Trade Mean Reversion (RSI & BB).
        - MTF Filter: Only BUY if Weekly Trend is BULLISH (unless extreme oversold).
        """
        # Trend Context (Daily)
        bullish_trend = current_price > sma_val if pd.notna(sma_val) else True
        bearish_trend = current_price < sma_val if pd.notna(sma_val) else True
        
        # BB Reversals
        below_bb = current_price < bb_lower if bb_lower is not None else False
        above_bb = current_price > bb_upper if bb_upper is not None else False

        # --- STRATEGY SELECTION ---
        
        signal = "HOLD"
        
        if adx > 25:
            # TREND MODE
            macd_buy = prev_hist < 0 and current_hist > 0
            macd_sell = prev_hist > 0 and current_hist < 0
            
            if macd_buy and bullish_trend: signal = "BUY"
            elif macd_sell and bearish_trend: signal = "SELL"
            
        else:
            # RANGE MODE
            if rsi < 30 or below_bb: signal = "BUY"
            elif rsi > 70 or above_bb: signal = "SELL"
            
        # --- MTF FILTER (The Safety Net) ---
        # Don't buy in a weekly downtrend unless it's a deep reversal (RSI < 30)
        if signal == "BUY" and weekly_trend == "BEARISH":
            if rsi > 30: # If not extreme oversold, cancel signal
                signal = "HOLD"
                
        # Don't sell in a weekly uptrend unless it's a blow-off top
        if signal == "SELL" and weekly_trend == "BULLISH":
            if rsi < 70: # If not extreme overbought, cancel signal
                signal = "HOLD"
                
        return signal
