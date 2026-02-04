import streamlit as st
import httpx
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# Configuration
API_URL = os.getenv("API_URL", "http://api:8000")
st.set_page_config(page_title="Charon Dashboard", layout="wide", page_icon="📈")

# Helper functions
def fetch_data(endpoint, params=None):
    try:
        with httpx.Client() as client:
            response = client.get(f"{API_URL}/{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        st.error(f"Error fetching data from {endpoint}: {e}")
        return []

def plot_mini_chart(title, prices_data, signals_data, height=400):
    """
    Creates a compact chart for the grid view.
    """
    if not prices_data:
        return None

    # Prepare DataFrames
    df_prices = pd.DataFrame(prices_data)
    if 'rate_mid' in df_prices.columns:
        df_prices = df_prices.rename(columns={'rate_mid': 'price', 'effective_date': 'date'})
    elif 'price' in df_prices.columns:
        df_prices = df_prices.rename(columns={'effective_date': 'date'})
    
    df_prices['date'] = pd.to_datetime(df_prices['date'])
    # Ensure date is tz-naive for merging
    if df_prices['date'].dt.tz is not None:
        df_prices['date'] = df_prices['date'].dt.tz_localize(None)
        
    df_prices = df_prices.sort_values('date')

    # MACD Calculation
    exp1 = df_prices['price'].ewm(span=12, adjust=False).mean()
    exp2 = df_prices['price'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal

    # Create subplots
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.08, 
                        row_heights=[0.7, 0.3])

    # Price Line
    fig.add_trace(go.Scatter(x=df_prices['date'], y=df_prices['price'], name='Price', line=dict(color='#2962FF', width=2)), row=1, col=1)

    # Add Signals
    if signals_data:
        df_signals = pd.DataFrame(signals_data)
        df_signals['generated_at'] = pd.to_datetime(df_signals['generated_at'])
        
        # Make timezone naive and normalize to midnight
        if df_signals['generated_at'].dt.tz is not None:
            df_signals['generated_at'] = df_signals['generated_at'].dt.tz_localize(None)
            
        df_signals['date'] = df_signals['generated_at'].dt.normalize()
        
        buys = df_signals[df_signals['signal'] == 'BUY']
        if not buys.empty:
            buys_on_chart = pd.merge(buys, df_prices, on='date', how='inner')
            fig.add_trace(go.Scatter(
                x=buys_on_chart['date'], y=buys_on_chart['price'],
                mode='markers', marker=dict(symbol='triangle-up', color='#00C853', size=10),
                name='BUY'
            ), row=1, col=1)

        sells = df_signals[df_signals['signal'] == 'SELL']
        if not sells.empty:
            sells_on_chart = pd.merge(sells, df_prices, on='date', how='inner')
            fig.add_trace(go.Scatter(
                x=sells_on_chart['date'], y=sells_on_chart['price'],
                mode='markers', marker=dict(symbol='triangle-down', color='#D50000', size=10),
                name='SELL'
            ), row=1, col=1)

    # MACD Histogram only for compactness
    colors = ['#00C853' if val >= 0 else '#D50000' for val in hist]
    fig.add_trace(go.Bar(x=df_prices['date'], y=hist, name='MACD Hist', marker_color=colors), row=2, col=1)

    # Latest Signal Text Annotation
    latest_signal = "NEUTRAL"
    if signals_data:
         latest_signal = signals_data[0]['signal'] # Assuming sorted DESC
    
    color_map = {"BUY": "green", "SELL": "red", "HOLD": "gray"}
    title_text = f"{title} <span style='color:{color_map.get(latest_signal, 'black')}'>({latest_signal})</span>"

    fig.update_layout(
        title=dict(text=title_text, x=0, font=dict(size=14)),
        height=height, 
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=False,
        template="plotly_white"
    )
    return fig

# Main UI
st.title("Charon: Market Overview")

tabs = st.tabs(["Markets", "Signals Log", "Miner Stats"])

with tabs[0]:
    st.markdown("### 🥇 Gold")
    gold_data = fetch_data("gold", {"limit": 180})
    gold_signals = fetch_data("signals", {"asset_code": "GOLD", "limit": 20})
    
    if gold_data:
        fig = plot_mini_chart("Gold Price (1g)", gold_data, gold_signals, height=450)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    st.markdown("### 💱 Currencies")
    
    currencies = fetch_data("currencies")
    
    if currencies:
        # Create a grid layout
        cols = st.columns(2) # 2 columns grid
        
        for idx, currency in enumerate(currencies):
            code = currency['code']
            name = currency['name']
            
            # Use columns in round-robin
            with cols[idx % 2]:
                # Fetch data for this currency
                # Limit history to 90 days for performance in grid view
                rates = fetch_data("rates", {"code": code, "limit": 90})
                signals = fetch_data("signals", {"asset_code": code, "limit": 10})
                
                if rates:
                    fig = plot_mini_chart(f"{code} - {name}", rates, signals, height=350)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning(f"No data for {code}")

with tabs[1]:
    st.header("Global Signals Log")
    all_signals = fetch_data("signals", {"limit": 100})
    if all_signals:
        df_sig = pd.DataFrame(all_signals)
        st.dataframe(
            df_sig[['generated_at', 'asset_code', 'signal', 'price_at_signal', 'histogram']],
            use_container_width=True
        )

with tabs[2]:
    st.header("Miner Status")
    stats = fetch_data("stats/miner")
    if stats:
        df_stats = pd.DataFrame(stats)
        st.dataframe(df_stats, use_container_width=True)
    
    if st.button("Refresh Miner Stats"):
        st.rerun()
