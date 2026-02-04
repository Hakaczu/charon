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

def plot_mini_chart(title, prices_data, signals_data, height=500):
    """
    Creates a compact chart with Price, MACD, and RSI.
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
    if df_prices['date'].dt.tz is not None:
        df_prices['date'] = df_prices['date'].dt.tz_localize(None)
    df_prices = df_prices.sort_values('date')

    # Indicators Calculation
    # 1. MACD
    exp1 = df_prices['price'].ewm(span=12, adjust=False).mean()
    exp2 = df_prices['price'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal_line

    # 2. SMA 50
    df_prices['sma50'] = df_prices['price'].rolling(window=50).mean()

    # 3. RSI
    delta = df_prices['price'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi_vals = 100 - (100 / (1 + rs))

    # Signal Info for Title
    latest_signal = "NEUTRAL"
    if signals_data:
         latest_signal = signals_data[0]['signal']
    
    color_map = {"BUY": "green", "SELL": "red", "HOLD": "gray"}
    title_text = f"{title} <span style='color:{color_map.get(latest_signal, 'black')}'>({latest_signal})</span>"

    # Create subplots
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.05, 
                        row_heights=[0.5, 0.25, 0.25])

    # Row 1: Price & SMA & Signals
    fig.add_trace(go.Scatter(x=df_prices['date'], y=df_prices['price'], name='Price', line=dict(color='#2962FF', width=2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_prices['date'], y=df_prices['sma50'], name='SMA 50', line=dict(color='#FF6D00', width=1, dash='dash')), row=1, col=1)

    if signals_data:
        df_signals = pd.DataFrame(signals_data)
        df_signals['generated_at'] = pd.to_datetime(df_signals['generated_at'])
        if df_signals['generated_at'].dt.tz is not None:
            df_signals['generated_at'] = df_signals['generated_at'].dt.tz_localize(None)
        df_signals['date'] = df_signals['generated_at'].dt.normalize()
        
        buys = df_signals[df_signals['signal'] == 'BUY']
        if not buys.empty:
            buys_on_chart = pd.merge(buys, df_prices, on='date', how='inner')
            fig.add_trace(go.Scatter(x=buys_on_chart['date'], y=buys_on_chart['price'], mode='markers', marker=dict(symbol='triangle-up', color='#00C853', size=10), name='BUY'), row=1, col=1)
        
        sells = df_signals[df_signals['signal'] == 'SELL']
        if not sells.empty:
            sells_on_chart = pd.merge(sells, df_prices, on='date', how='inner')
            fig.add_trace(go.Scatter(x=sells_on_chart['date'], y=sells_on_chart['price'], mode='markers', marker=dict(symbol='triangle-down', color='#D50000', size=10), name='SELL'), row=1, col=1)

    # Row 2: MACD Histogram
    macd_colors = ['#00C853' if val >= 0 else '#D50000' for val in hist]
    fig.add_trace(go.Bar(x=df_prices['date'], y=hist, name='MACD Hist', marker_color=macd_colors), row=2, col=1)

    # Row 3: RSI
    fig.add_trace(go.Scatter(x=df_prices['date'], y=rsi_vals, name='RSI', line=dict(color='#7E57C2', width=1.5)), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)

    # Styling and Zoom
    if not df_prices.empty:
        last_date = df_prices['date'].max()
        start_view_date = last_date - pd.Timedelta(days=365)
        fig.update_xaxes(range=[start_view_date, last_date])

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

tabs = st.tabs(["Markets", "Signals Log", "Miner Stats", "Backtesting"])

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
                    df_temp = pd.DataFrame(data) # Use all data for correct rolling calc
                    if 'rate_mid' in df_temp.columns: col_p = 'rate_mid' 
                    else: col_p = 'price'
                    
                    df_temp[col_p] = df_temp[col_p].astype(float)
                    
                    # Volatility
                    volatility = df_temp[col_p].iloc[:10].std()
                    
                    # SMA 50
                    sma50_val = df_temp[col_p].iloc[:50].mean() if len(df_temp) >= 50 else 0
                    price_rel_sma = "Above" if last_price > sma50_val else "Below"
                    sma_color = "green" if price_rel_sma == "Above" else "red"
                    
                    # RSI (Calculate locally for stats display)
                    delta = df_temp[col_p].diff()
                    # Reversing data for calculation might be tricky if data comes DESC/ASC. 
                    # Assuming data is DESC from API usually, but let's sort ASC for calc then back.
                    # Actually, plot_mini_chart sorts it. Let's do it safely here.
                    df_calc = df_temp.sort_values('effective_date' if 'effective_date' in df_temp.columns else 'fetched_at')
                    delta = df_calc[col_p].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    rs = gain / loss
                    rsi_series = 100 - (100 / (1 + rs))
                    
                    last_rsi = float(rsi_series.iloc[-1]) if not rsi_series.empty and not pd.isna(rsi_series.iloc[-1]) else 50
                    
                    rsi_state = "Neutral"
                    rsi_color = "gray"
                    if last_rsi >= 70: 
                        rsi_state = "Overbought"
                        rsi_color = "red"
                    elif last_rsi <= 30:
                        rsi_state = "Oversold"
                        rsi_color = "green"

                    s_col1.caption("Latest Signal")
                    if last_sig == "BUY": s_col1.success(last_sig)
                    elif last_sig == "SELL": s_col1.error(last_sig)
                    else: s_col1.info(last_sig)
                    
                    s_col2.caption("Indicators")
                    s_col2.write(f"**P: {last_price:.4f}** | V: {volatility:.3f}")
                    s_col2.markdown(f"SMA50: <span style='color:{sma_color}'>{price_rel_sma}</span>", unsafe_allow_html=True)
                    s_col2.markdown(f"RSI: {last_rsi:.1f} (<span style='color:{rsi_color}'>{rsi_state}</span>)", unsafe_allow_html=True)
                
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
    
    # Upcoming Jobs Section
    upcoming = fetch_data("stats/upcoming")
    if upcoming:
        u_col1, u_col2, u_col3 = st.columns(3)
        
        # Parse strings to datetime for nicer formatting if needed, or just display
        next_rates = pd.to_datetime(upcoming.get('import_rates')).strftime('%H:%M:%S')
        next_gold = pd.to_datetime(upcoming.get('import_gold')).strftime('%H:%M:%S')
        server_time = pd.to_datetime(upcoming.get('server_time')).strftime('%H:%M:%S')

        u_col1.metric("Next Rates Import", next_rates)
        u_col2.metric("Next Gold Import", next_gold)
        u_col3.metric("Server Time", server_time)
    
    st.divider()
    
    # Existing Stats Table
    stats = fetch_data("stats/miner")
    if stats:
        df_stats = pd.DataFrame(stats)
        st.dataframe(df_stats, use_container_width=True)
    
    if st.button("Refresh Miner Stats"):
        st.rerun()

with tabs[3]:
    st.header("Strategy Backtesting")
    
    col_b1, col_b2, col_b3 = st.columns([1, 1, 1])
    with col_b1:
        # Asset Selection
        b_currencies = fetch_data("currencies")
        b_options = ["GOLD"] + [c['code'] for c in b_currencies] if b_currencies else ["GOLD", "USD", "EUR"]
        b_asset = st.selectbox("Select Asset to Test", b_options)
        
    with col_b2:
        b_capital = st.number_input("Initial Capital (PLN)", value=10000, step=1000)
        
    with col_b3:
        st.write("")
        st.write("")
        run_btn = st.button("🚀 Run Simulation", type="primary")

    if run_btn:
        with st.spinner("Running simulation on historical data..."):
            try:
                # POST request to backtest
                with httpx.Client() as client:
                    resp = client.post(
                        f"{API_URL}/backtest", 
                        params={"asset_code": b_asset, "initial_capital": b_capital}
                    )
                    if resp.status_code == 200:
                        res = resp.json()
                        
                        # Metrics
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Final Value", f"{res['final_value']:.2f} PLN", f"{res['total_return_pct']:.2f}%")
                        m2.metric("Total Trades", res['total_trades'])
                        profit = res['final_value'] - res['initial_capital']
                        m3.metric("Profit/Loss", f"{profit:.2f} PLN")
                        
                        # Equity Curve
                        equity_data = res.get('equity_curve', [])
                        if equity_data:
                            df_eq = pd.DataFrame(equity_data)
                            df_eq['date'] = pd.to_datetime(df_eq['date'])
                            
                            fig_eq = go.Figure()
                            fig_eq.add_trace(go.Scatter(x=df_eq['date'], y=df_eq['equity'], mode='lines', name='Equity', fill='tozeroy'))
                            fig_eq.update_layout(title="Portfolio Value Over Time", template="plotly_white", height=400)
                            st.plotly_chart(fig_eq, use_container_width=True)
                            
                        # Trades Table
                        trades_data = res.get('trades', [])
                        if trades_data:
                            st.subheader("Trade History")
                            df_trades = pd.DataFrame(trades_data)
                            st.dataframe(df_trades, use_container_width=True)
                        else:
                            st.info("No trades were executed in this period.")
                            
                    else:
                        st.error(f"Simulation failed: {resp.text}")
            except Exception as e:
                st.error(f"Error: {e}")
