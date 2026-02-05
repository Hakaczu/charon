import streamlit as st
import httpx
import pandas as pd
import numpy as np
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

    # 4. Bollinger Bands
    sma20 = df_prices['price'].rolling(window=20).mean()
    std20 = df_prices['price'].rolling(window=20).std()
    bb_upper = sma20 + (2 * std20)
    bb_lower = sma20 - (2 * std20)

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

    # Row 1: Price & SMA & Signals & BB
    # BB Lower (invisible line for fill anchor)
    fig.add_trace(go.Scatter(x=df_prices['date'], y=bb_lower, line=dict(width=0), showlegend=False, hoverinfo='skip'), row=1, col=1)
    # BB Upper (fill down to lower)
    fig.add_trace(go.Scatter(x=df_prices['date'], y=bb_upper, fill='tonexty', fillcolor='rgba(128, 128, 128, 0.1)', line=dict(width=0), showlegend=False, hoverinfo='skip'), row=1, col=1)
    
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

tabs = st.tabs(["Markets", "Signals Log", "Miner Stats", "Backtesting", "Analysis", "Finances"])

with tabs[0]:
    # --- EXECUTIVE SUMMARY ---
    summary_container = st.container(border=True)
    with summary_container:
        st.subheader("📢 Market Executive Summary")
        
        # 1. Gather Data for Summary
        summ_assets = ["GOLD", "USD", "EUR", "CHF", "GBP", "JPY", "CAD", "AUD", "NOK"]
        up_count = 0
        down_count = 0
        top_gainer = {"code": None, "pct": -999}
        top_loser = {"code": None, "pct": 999}
        rsi_alerts = []
        featured_signal = None
        
        for code in summ_assets:
            endpoint = "gold" if code == "GOLD" else "rates"
            params = {"limit": 2}
            if code != "GOLD": params["code"] = code
            data = fetch_data(endpoint, params)
            
            if data and len(data) > 1:
                curr = float(data[0].get('rate_mid', data[0].get('price')))
                prev = float(data[1].get('rate_mid', data[1].get('price')))
                change_pct = ((curr - prev) / prev) * 100
                
                if change_pct > 0: up_count += 1
                else: down_count += 1
                
                if change_pct > top_gainer["pct"]: top_gainer = {"code": code, "pct": change_pct}
                if change_pct < top_loser["pct"]: top_loser = {"code": code, "pct": change_pct}
                
                # Check RSI (need more history for this, let's skip rigorous calculation here to save time 
                # or fetch latest signal to see if it has RSI snapshot)
                # Actually we can check recent signals
        
        # Fetch latest signals for alerts
        sigs = fetch_data("signals", {"limit": 20})
        if sigs:
            for s in sigs:
                if s['asset_code'] in summ_assets and not featured_signal:
                    if s['signal'] == "BUY": featured_signal = s
                
                # Check RSI from signal snapshot if available (some old signals might not have it)
                if 'rsi' in s and s['rsi']:
                    rsi_val = float(s['rsi'])
                    if rsi_val > 70: rsi_alerts.append(f"**{s['asset_code']}** is Overbought (RSI {rsi_val:.0f})")
                    if rsi_val < 30: rsi_alerts.append(f"**{s['asset_code']}** is Oversold (RSI {rsi_val:.0f})")

        # 2. Generate Text
        sentiment = "Neutral"
        if up_count > down_count + 2: sentiment = "Bullish (Growth)"
        elif down_count > up_count + 2: sentiment = "Bearish (Decline)"
        
        col_sum1, col_sum2 = st.columns([3, 1])
        
        with col_sum1:
            st.markdown(f"**Market Sentiment:** {sentiment}")
            st.write(f"Today, **{up_count}** assets are up and **{down_count}** are down.")
            
            movers_text = ""
            if top_gainer['code']: movers_text += f"🚀 Top Gainer: **{top_gainer['code']}** (+{top_gainer['pct']:.2f}%)  "
            if top_loser['code']: movers_text += f"📉 Top Loser: **{top_loser['code']}** ({top_loser['pct']:.2f}%)"
            st.markdown(movers_text)
            
            if rsi_alerts:
                st.markdown("⚠️ **Alerts:** " + ", ".join(list(set(rsi_alerts))[:3])) # limit to 3 unique
        
        with col_sum2:
            if featured_signal:
                st.info(f"💡 **Signal of the Day**\n\n**{featured_signal['asset_code']}**\n\nAction: **{featured_signal['signal']}**\n\nDate: {featured_signal['generated_at'][:10]}")
            else:
                st.info("💡 **Signal of the Day**\n\nNo strong signals generated recently.")

    # --- TICKER / METRICS ROW ---
    st.markdown("### 📊 Market Snapshot")
    
    top_assets = ["GOLD", "USD", "EUR", "CHF", "GBP", "JPY", "CAD", "AUD", "NOK"]
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
    
    # 2. Add Top 7 Currencies only + NOK
    currencies = fetch_data("currencies")
    if currencies:
        PRIORITY_ORDER = ["USD", "EUR", "CHF", "GBP", "JPY", "CAD", "AUD", "NOK"]
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

with tabs[4]:
    st.header("Advanced Market Analysis")
    
    a_col1, a_col2, a_col3, a_col4 = st.tabs(["🔥 Correlation", "📅 Seasonality", "🔮 AI Forecast", "💰 Profit Calc"])
    
    # --- 1. CORRELATION ---
    with a_col1:
        st.subheader("Market Correlation Matrix (180 days)")
        st.write("Correlation matrix based on the last 180 days of price data.")
        with st.spinner("Calculating correlation matrix..."):
            corr_data = fetch_data("stats/correlation")
            if corr_data:
                df_corr = pd.DataFrame(corr_data)
                fig_corr = go.Figure(data=go.Heatmap(
                    z=df_corr.values, x=df_corr.columns, y=df_corr.index,
                    colorscale='RdBu', zmin=-1, zmax=1,
                    text=df_corr.round(2).values, texttemplate="%{text}", hoverongaps=False
                ))
                fig_corr.update_layout(height=600, xaxis_showgrid=False, yaxis_showgrid=False)
                st.plotly_chart(fig_corr, use_container_width=True)
                st.info("**1.0 (Dark Blue):** Perfect positive correlation. **-1.0 (Dark Red):** Perfect negative correlation.")
            else:
                st.warning("Not enough data.")

    # --- 2. SEASONALITY ---
    with a_col2:
        st.subheader("Monthly Seasonality Heatmap")
        st.write("Analyze historical monthly returns to identify seasonal patterns.")
        
        s_asset = st.selectbox("Select Asset", ["GOLD", "USD", "EUR", "CHF", "GBP", "JPY", "CAD", "AUD", "NOK"], key="seas_asset")
        
        if st.button("Analyze Seasonality"):
            with st.spinner("Crunching historical numbers..."):
                seas_data = fetch_data("stats/seasonality", {"asset_code": s_asset})
                if seas_data:
                    df_seas = pd.DataFrame(seas_data)
                    df_seas = df_seas.set_index('year')
                    
                    z_vals = df_seas.values
                    y_vals = df_seas.index
                    x_vals = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                    
                    fig_seas = go.Figure(data=go.Heatmap(
                        z=z_vals, x=x_vals, y=y_vals,
                        colorscale='RdYlGn', zmid=0,
                        text=np.round(z_vals, 1), texttemplate="%{text}%%", hoverongaps=False
                    ))
                    fig_seas.update_layout(height=600, yaxis=dict(title='Year', autorange='reversed'), xaxis=dict(title='Month'))
                    st.plotly_chart(fig_seas, use_container_width=True)
                    
                    avg_monthly = df_seas.mean(axis=0)
                    fig_avg = go.Figure()
                    fig_avg.add_trace(go.Bar(x=x_vals, y=avg_monthly.values, marker_color=['green' if v > 0 else 'red' for v in avg_monthly.values]))
                    fig_avg.update_layout(title="Average Monthly Return", height=300)
                    st.plotly_chart(fig_avg, use_container_width=True)
                else:
                    st.error("No seasonality data found.")

    # --- 3. AI FORECAST ---
    with a_col3:
        st.subheader("AI Price Forecasting (Prophet)")
        f_assets = ["GOLD", "USD", "EUR", "CHF", "GBP", "JPY", "CAD", "AUD", "NOK"]
        f_asset = st.selectbox("Select Asset to Forecast", f_assets, key="ai_asset_sel")
        if st.button("🔮 Run AI Forecast", type="primary"):
            with st.spinner(f"Training AI model for {f_asset}..."):
                try:
                    f_data = fetch_data("predict", {"asset_code": f_asset, "days": 7})
                    if f_data:
                        df_f = pd.DataFrame(f_data)
                        df_f['ds'] = pd.to_datetime(df_f['ds'])
                        fig_f = go.Figure()
                        fig_f.add_trace(go.Scatter(
                            x=df_f['ds'].tolist() + df_f['ds'].tolist()[::-1],
                            y=df_f['yhat_upper'].tolist() + df_f['yhat_lower'].tolist()[::-1],
                            fill='toself', fillcolor='rgba(0,176,246,0.2)', line=dict(color='rgba(255,255,255,0)'), name='Uncertainty'
                        ))
                        fig_f.add_trace(go.Scatter(x=df_f['ds'], y=df_f['yhat'], line=dict(color='rgb(0,176,246)'), name='Predicted Price'))
                        fig_f.update_layout(title=f"7-Day Forecast for {f_asset}", template="plotly_white", height=400)
                        st.plotly_chart(fig_f, use_container_width=True)
                    else:
                        st.error("Prediction failed.")
                except Exception as e:
                    st.error(f"Error: {e}")

    # --- 4. INVESTMENT CALCULATOR ---
    with a_col4:
        st.subheader("Investment Profit Calculator")
        calc_amount = st.number_input("Investment Amount (PLN)", value=1000, step=100, key="inv_amount_calc")
        
        all_latest_signals = fetch_data("signals", {"limit": 100})
        if all_latest_signals:
            target_assets = ["GOLD", "USD", "EUR", "CHF", "GBP", "JPY", "CAD", "AUD", "NOK"]
            latest_buys = {}
            for s in all_latest_signals:
                if s['asset_code'] in target_assets and s['signal'] == "BUY" and s['asset_code'] not in latest_buys:
                    latest_buys[s['asset_code']] = s
            
            if latest_buys:
                calc_cols = st.columns(4)
                for idx, (code, signal_data) in enumerate(latest_buys.items()):
                    endpoint = "gold" if code == "GOLD" else "rates"
                    params = {"limit": 1}
                    if code != "GOLD": params["code"] = code
                    curr_data = fetch_data(endpoint, params)
                    if curr_data:
                        current_price = float(curr_data[0].get('rate_mid', curr_data[0].get('price')))
                        buy_price = float(signal_data['price_at_signal'])
                        units = calc_amount / buy_price
                        current_value = units * current_price
                        profit = current_value - calc_amount
                        profit_pct = (profit / calc_amount) * 100
                        with calc_cols[idx % 4]:
                            with st.container(border=True):
                                st.write(f"**{code}**")
                                st.caption(f"Bought at: {buy_price:.4f}")
                                st.metric("Value", f"{current_value:.2f}", f"{profit_pct:.2f}%")
                                st.write(f"Profit: **{profit:.2f} PLN**")
            else:
                st.info("No active BUY signals found.")
        else:
            st.warning("Could not fetch signals.")



