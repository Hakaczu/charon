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

    # SMA 50 Calculation (Simple Moving Average)
    df_prices['sma50'] = df_prices['price'].rolling(window=50).mean()

    # Create subplots
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.08, 
                        row_heights=[0.7, 0.3])

    # Price Line
    fig.add_trace(go.Scatter(x=df_prices['date'], y=df_prices['price'], name='Price', line=dict(color='#2962FF', width=2)), row=1, col=1)
    
    # SMA 50 Line
    fig.add_trace(go.Scatter(x=df_prices['date'], y=df_prices['sma50'], name='SMA 50', line=dict(color='#FF6D00', width=1, dash='dash')), row=1, col=1)

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

    # Histogram colors
    colors = ['#00C853' if val >= 0 else '#D50000' for val in hist]
    fig.add_trace(go.Bar(x=df_prices['date'], y=hist, name='MACD Hist', marker_color=colors), row=2, col=1)

    # Set default zoom to last 365 days
    if not df_prices.empty:
        last_date = df_prices['date'].max()
        start_view_date = last_date - pd.Timedelta(days=365)
        fig.update_xaxes(range=[start_view_date, last_date])

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
    # --- TICKER / METRICS ROW ---
    st.markdown("### 📊 Market Snapshot")
    
    top_assets = ["GOLD", "USD", "EUR", "CHF", "GBP", "JPY", "CAD", "AUD"]
    cols = st.columns(len(top_assets))
    
    for idx, asset_code in enumerate(top_assets):
        # Fetch minimal data for metric (last 2 days for delta)
        endpoint = "gold" if asset_code == "GOLD" else "rates"
        params = {"limit": 2}
        if asset_code != "GOLD":
            params["code"] = asset_code
            
        data = fetch_data(endpoint, params)
        
        # Fetch latest signal
        sig_data = fetch_data("signals", {"asset_code": asset_code, "limit": 1})
        latest_signal = sig_data[0]['signal'] if sig_data else "WAIT"
        
        with cols[idx]:
            if data and len(data) > 0:
                curr = data[0]
                price = float(curr.get('rate_mid', curr.get('price')))
                
                # Calculate Delta
                delta_val = 0
                delta_pct = 0
                if len(data) > 1:
                    prev = data[1]
                    prev_price = float(prev.get('rate_mid', prev.get('price')))
                    delta_val = price - prev_price
                    delta_pct = (delta_val / prev_price) * 100
                
                # Signal Icon
                sig_icon = "⚪"
                if latest_signal == "BUY": sig_icon = "🟢 BUY"
                elif latest_signal == "SELL": sig_icon = "🔴 SELL"
                elif latest_signal == "HOLD": sig_icon = "🟡 HOLD"
                
                st.metric(
                    label=f"{asset_code}",
                    value=f"{price:.4f}",
                    delta=f"{delta_pct:.2f}%"
                )
                st.caption(f"{sig_icon}")
            else:
                st.metric(label=asset_code, value="---")

    st.divider()

    # --- CHARTS GRID ---
    st.markdown("### 📉 Market Charts")
    
    # Combine Gold + All Currencies into one list for grid display
    # We want Gold first, then currencies
    grid_items = []
    
    # 1. Add Gold
    grid_items.append({
        'code': 'GOLD',
        'name': 'Gold (1g)',
        'type': 'gold'
    })
    
    # 2. Add Top 7 Currencies only
    currencies = fetch_data("currencies")
    if currencies:
        PRIORITY_ORDER = ["USD", "EUR", "CHF", "GBP", "JPY", "CAD", "AUD"]
        curr_map = {c['code']: c for c in currencies}
        
        for p_code in PRIORITY_ORDER:
            if p_code in curr_map:
                c = curr_map[p_code]
                grid_items.append({
                    'code': c['code'],
                    'name': c['name'],
                    'type': 'currency'
                })
            
    # Display in 3 columns (Grid is now limited to 8 items total: Gold + 7 currencies)
    cols = st.columns(3)
    
    for idx, item in enumerate(grid_items):
        code = item['code']
        name = item['name']
        
        with cols[idx % 3]:
            # Fetch data - set limit to 5000 to capture full available history
            endpoint = "gold" if item['type'] == 'gold' else "rates"
            params = {"limit": 5000} if item['type'] == 'gold' else {"code": code, "limit": 5000}
            
            data = fetch_data(endpoint, params)
            signals = fetch_data("signals", {"asset_code": code, "limit": 10})
            
            if data:
                # Plot
                fig = plot_mini_chart(f"{code}", data, signals, height=350)
                st.plotly_chart(fig, use_container_width=True)
                
                # Stats Section below chart using native Streamlit containers
                with st.container(border=True):
                    s_col1, s_col2 = st.columns(2)
                    
                    last_price = float(data[0].get('rate_mid', data[0].get('price')))
                    last_sig = signals[0]['signal'] if signals else "NONE"
                    
                    # Calculate simple volatility (std dev of last 10 days)
                    df_temp = pd.DataFrame(data[:50]) # Need 50 for SMA
                    if 'rate_mid' in df_temp.columns: col_p = 'rate_mid' 
                    else: col_p = 'price'
                    
                    df_temp[col_p] = df_temp[col_p].astype(float)
                    volatility = df_temp[col_p].iloc[:10].std()
                    
                    # Current SMA 50 from data (if enough rows)
                    sma50_val = df_temp[col_p].mean() if len(df_temp) >= 50 else 0
                    price_rel_sma = "Above" if last_price > sma50_val else "Below"
                    sma_color = "green" if price_rel_sma == "Above" else "red"

                    s_col1.caption("Latest Signal")
                    if last_sig == "BUY": s_col1.success(last_sig)
                    elif last_sig == "SELL": s_col1.error(last_sig)
                    else: s_col1.info(last_sig)
                    
                    s_col2.caption("Price, Vol & SMA")
                    s_col2.write(f"**{last_price:.4f}** (V: {volatility:.3f})")
                    if sma50_val > 0:
                        s_col2.markdown(f"SMA50: {sma50_val:.4f} (<span style='color:{sma_color}'>{price_rel_sma}</span>)", unsafe_allow_html=True)
                    else:
                        s_col2.write("SMA50: N/A")
                
                st.markdown("<br>", unsafe_allow_html=True) # Spacer
            else:
                st.warning(f"No data for {code}")

with tabs[1]:
    st.header("Global Signals Log")
    all_signals = fetch_data("signals", {"limit": 100})
    if all_signals:
        df_sig = pd.DataFrame(all_signals)
        df_display = df_sig[['generated_at', 'asset_code', 'signal', 'price_at_signal', 'histogram']].copy()
        
        def color_signal_text(val):
            if val == "BUY": color = '#00FF00' # Bright Green
            elif val == "SELL": color = '#FF0000' # Bright Red
            else: color = '#888888' # Gray
            return f'color: {color}; font-weight: bold'

        st.dataframe(
            df_display.style.applymap(color_signal_text, subset=['signal']),
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
