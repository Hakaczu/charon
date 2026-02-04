import pandas as pd
from typing import List, Dict, Any
from .analysis import TechnicalAnalyzer

class Backtester:
    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.analyzer = TechnicalAnalyzer()

    def run(self, df_prices: pd.DataFrame) -> Dict[str, Any]:
        """
        Runs the backtest simulation.
        df_prices must have 'date' and 'price' columns and be sorted ascending by date.
        """
        capital = self.initial_capital
        position = 0.0 # Amount of asset held
        equity_curve = []
        trades = []
        
        # Pre-calculate indicators for the whole series to speed up lookups
        # (In real-time trading we calculate step-by-step, but here vectorized calc is safe 
        # as long as we access index i using data up to i)
        
        # Ensure we have enough data
        if len(df_prices) < 50:
            return {"error": "Not enough data for backtest (min 50 days)"}

        # Calculate indicators over full history
        prices_series = df_prices['price']
        macd_df = self.analyzer.calculate_macd(prices_series)
        rsi_series = self.analyzer.calculate_rsi(prices_series)
        sma_series = self.analyzer.calculate_sma(prices_series, window=50)
        bb_df = self.analyzer.calculate_bollinger_bands(prices_series)
        
        # Merge all into one df for easier iteration
        df = df_prices.copy()
        df['macd'] = macd_df['macd']
        df['signal_line'] = macd_df['signal']
        df['hist'] = macd_df['hist']
        df['rsi'] = rsi_series
        df['sma'] = sma_series
        df['bb_lower'] = bb_df['bb_lower']
        df['bb_upper'] = bb_df['bb_upper']
        
        # Iterate starting from day 50 (to have SMA/MACD valid)
        for i in range(50, len(df)):
            row = df.iloc[i]
            prev_row = df.iloc[i-1]
            prev2_row = df.iloc[i-2] # Need prev-prev for crossover check sometimes
            
            date = row['date']
            price = row['price']
            
            # Logic Context
            curr_hist = row['hist']
            prev_hist = prev_row['hist']
            curr_rsi = row['rsi']
            curr_sma = row['sma']
            curr_bb_lower = row['bb_lower']
            curr_bb_upper = row['bb_upper']
            
            # Re-use the EXACT logic from TechnicalAnalyzer
            # Note: The analyzer function expects pure floats
            signal = self.analyzer.determine_signal(
                current_hist=float(curr_hist),
                prev_hist=float(prev_hist),
                rsi=float(curr_rsi),
                current_price=float(price),
                sma_val=float(curr_sma),
                bb_lower=float(curr_bb_lower),
                bb_upper=float(curr_bb_upper)
            )
            
            # Execute Trade
            if signal == "BUY" and position == 0:
                # Buy with all capital
                position = capital / price
                capital = 0
                trades.append({
                    "date": date,
                    "type": "BUY",
                    "price": price,
                    "value": position * price
                })
            
            elif signal == "SELL" and position > 0:
                # Sell all position
                capital = position * price
                position = 0
                trades.append({
                    "date": date,
                    "type": "SELL",
                    "price": price,
                    "value": capital
                })
            
            # Record Equity
            current_value = capital + (position * price)
            equity_curve.append({
                "date": date,
                "equity": current_value,
                "drawdown": 0 # TODO calc drawdown
            })

        # Finalize
        final_value = capital + (position * df.iloc[-1]['price'])
        total_return_pct = ((final_value - self.initial_capital) / self.initial_capital) * 100
        
        return {
            "initial_capital": self.initial_capital,
            "final_value": final_value,
            "total_return_pct": total_return_pct,
            "total_trades": len(trades),
            "trades": trades,
            "equity_curve": equity_curve
        }
