import streamlit as st
import httpx
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import datetime

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

def plot_asset(title, prices_data, signals_data, asset_name):
    if not prices_data:
        st.warning(f"No data for {asset_name}")
        return

    # Prepare DataFrames
    df_prices = pd.DataFrame(prices_data)
    if 'rate_mid' in df_prices.columns:
        df_prices = df_prices.rename(columns={'rate_mid': 'price', 'effective_date': 'date'})
    elif 'price' in df_prices.columns:
        df_prices = df_prices.rename(columns={'effective_date': 'date'})
    
    df_prices['date'] = pd.to_datetime(df_prices['date'])
    df_prices = df_prices.sort_values('date')

    # Create subplots
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.03, subplot_titles=(f'{title} Price', 'MACD'),
                        row_heights=[0.7, 0.3])

    # Price Line
    fig.add_trace(go.Scatter(x=df_prices['date'], y=df_prices['price'], name='Price'), row=1, col=1)

    # Add Buy/Sell markers if signals exist
    if signals_data:
        df_signals = pd.DataFrame(signals_data)
        df_signals['generated_at'] = pd.to_datetime(df_signals['generated_at'])
        # Filter signals for this asset mostly happens on backend, but ensuring here
        
        # We need to map signals to price dates approx or just plot on generated_at
        # For simplicity, let's just plot markers on the price chart where signal generated_at matches close to date
        # Or easier: just listing signals in a table below.
        pass

    # Fake MACD calculation for visualization if API doesn't return full history of MACD
    # (The Brain calculates it, but the API /rates endpoint currently returns only prices)
    # We can recalculate here for display or extend API. 
    # Let's recalculate purely for the chart visualization to match Brain's logic.
    exp1 = df_prices['price'].ewm(span=12, adjust=False).mean()
    exp2 = df_prices['price'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal

    fig.add_trace(go.Scatter(x=df_prices['date'], y=macd, name='MACD'), row=2, col=1)
    fig.add_trace(go.Scatter(x=df_prices['date'], y=signal, name='Signal'), row=2, col=1)
    fig.add_trace(go.Bar(x=df_prices['date'], y=hist, name='Histogram'), row=2, col=1)

    fig.update_layout(height=600, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

# Main UI
st.title("Charon: Currency & Gold Trends")

tabs = st.tabs(["Dashboard", "Gold", "Signals", "Miner Stats"])

with tabs[0]:
    st.header("Currency Analysis")
    currencies = fetch_data("currencies")
    
    if currencies:
        options = {c['code']: f"{c['code']} - {c['name']}" for c in currencies}
        selected_code = st.selectbox("Select Currency", list(options.keys()), format_func=lambda x: options[x])
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            rates = fetch_data("rates", {"code": selected_code, "limit": 200})
            plot_asset(selected_code, rates, None, selected_code)
            
        with col2:
            st.subheader("Latest Signals")
            signals = fetch_data("signals", {"asset_code": selected_code, "limit": 5})
            for s in signals:
                color = "green" if s['signal'] == "BUY" else "red" if s['signal'] == "SELL" else "gray"
                st.markdown(f"**{s['signal']}** : {s['generated_at'][:10]}")
                st.caption(f"Price: {s['price_at_signal']}")
                st.divider()

with tabs[1]:
    st.header("Gold Market")
    gold_data = fetch_data("gold", {"limit": 200})
    
    col1, col2 = st.columns([3, 1])
    with col1:
        plot_asset("Gold 1g", gold_data, None, "Gold")
    with col2:
        st.subheader("Latest Signals")
        signals = fetch_data("signals", {"asset_code": "GOLD", "limit": 5})
        for s in signals:
            color = "green" if s['signal'] == "BUY" else "red" if s['signal'] == "SELL" else "gray"
            st.markdown(f"**{s['signal']}** : {s['generated_at'][:10]}")
            st.caption(f"Price: {s['price_at_signal']}")
            st.divider()

with tabs[2]:
    st.header("All Signals Log")
    all_signals = fetch_data("signals", {"limit": 50})
    if all_signals:
        df_sig = pd.DataFrame(all_signals)
        st.dataframe(df_sig[['generated_at', 'asset_code', 'signal', 'price_at_signal', 'histogram']])

with tabs[3]:
    st.header("Miner Status")
    stats = fetch_data("stats/miner")
    if stats:
        df_stats = pd.DataFrame(stats)
        st.dataframe(df_stats)
    
    if st.button("Refresh Data"):
        st.rerun()
