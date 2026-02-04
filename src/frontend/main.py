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

with tabs[4]:
    st.header("Market Correlation Analysis")
    st.write("Correlation matrix based on the last 180 days of price data.")
    
    with st.spinner("Calculating correlation matrix..."):
        corr_data = fetch_data("stats/correlation")
        
        if corr_data:
            df_corr = pd.DataFrame(corr_data)
            
            # Create Plotly Heatmap
            fig_corr = go.Figure(data=go.Heatmap(
                z=df_corr.values,
                x=df_corr.columns,
                y=df_corr.index,
                colorscale='RdBu', # Red-Blue scale (Red = Negative, Blue = Positive)
                zmin=-1, zmax=1,
                text=df_corr.round(2).values,
                texttemplate="%{text}",
                hoverongaps=False
            ))
            
            fig_corr.update_layout(
                title="Asset Correlation Heatmap (Pearson)",
                height=600,
                xaxis_showgrid=False,
                yaxis_showgrid=False
            )
            
            st.plotly_chart(fig_corr, use_container_width=True)
            
            st.info("""
            **How to read this?**
            * **1.0 (Dark Blue):** Perfect positive correlation (move together).
            * **-1.0 (Dark Red):** Perfect negative correlation (move in opposite directions).
            * **0.0 (White):** No correlation.
            """)

    st.divider()
    st.header("💰 Investment Profit Calculator")
    st.write("Calculates hypothetical profit if you had invested at the time of the latest **BUY** signal.")
    
    calc_amount = st.number_input("Investment Amount (PLN)", value=1000, step=100)
    
    # Get all latest signals
    all_latest_signals = fetch_data("signals", {"limit": 100})
    if all_latest_signals:
        target_assets = ["GOLD", "USD", "EUR", "CHF", "GBP", "JPY", "CAD", "AUD"]
        
        # Filter to only the most recent BUY signal per TARGET asset
        latest_buys = {}
        for s in all_latest_signals:
            if s['asset_code'] in target_assets and s['signal'] == "BUY" and s['asset_code'] not in latest_buys:
                latest_buys[s['asset_code']] = s
        
        if latest_buys:
            calc_cols = st.columns(4)
            for idx, (code, signal_data) in enumerate(latest_buys.items()):
                # Fetch current price
                endpoint = "gold" if code == "GOLD" else "rates"
                params = {"limit": 1}
                if code != "GOLD": params["code"] = code
                curr_data = fetch_data(endpoint, params)
                
                if curr_data:
                    current_price = float(curr_data[0].get('rate_mid', curr_data[0].get('price')))
                    buy_price = float(signal_data['price_at_signal'])
                    
                    # Calculation
                    units = calc_amount / buy_price
                    current_value = units * current_price
                    profit = current_value - calc_amount
                    profit_pct = (profit / calc_amount) * 100
                    
                    with calc_cols[idx % 4]:
                        with st.container(border=True):
                            st.write(f"**{code}**")
                            st.caption(f"Bought at: {buy_price:.4f}")
                            st.metric("Current Value", f"{current_value:.2f}", f"{profit_pct:.2f}%")
                            st.write(f"Profit: **{profit:.2f} PLN**")
        else:
            st.info("No active BUY signals found in the recent history to calculate from.")
    else:
        st.warning("Could not fetch signals for calculation.")

    st.divider()
    st.header("🔮 AI Price Forecasting (Prophet)")
    st.write("AI-powered prediction of future price trends for the next 7 days.")
    
    f_assets = ["GOLD", "USD", "EUR", "CHF", "GBP", "JPY", "CAD", "AUD"]
    f_asset = st.selectbox("Select Asset to Forecast", f_assets)
    
    if st.button("🔮 Run AI Forecast", type="primary"):
        with st.spinner(f"Training AI model for {f_asset}... This may take a moment."):
            try:
                # API Call
                f_data = fetch_data("predict", {"asset_code": f_asset, "days": 7})
                
                if f_data:
                    df_f = pd.DataFrame(f_data)
                    df_f['ds'] = pd.to_datetime(df_f['ds'])
                    
                    # Create Forecast Chart
                    fig_f = go.Figure()
                    
                    # Uncertainty Interval
                    fig_f.add_trace(go.Scatter(
                        x=df_f['ds'].tolist() + df_f['ds'].tolist()[::-1],
                        y=df_f['yhat_upper'].tolist() + df_f['yhat_lower'].tolist()[::-1],
                        fill='toself',
                        fillcolor='rgba(0,176,246,0.2)',
                        line=dict(color='rgba(255,255,255,0)'),
                        hoverinfo="skip",
                        showlegend=False,
                        name='Uncertainty'
                    ))
                    
                    # Predicted line
                    fig_f.add_trace(go.Scatter(
                        x=df_f['ds'], y=df_f['yhat'],
                        line=dict(color='rgb(0,176,246)'),
                        name='Predicted Price'
                    ))
                    
                    fig_f.update_layout(
                        title=f"7-Day Forecast for {f_asset}",
                        template="plotly_white",
                        yaxis_title="Estimated Price",
                        height=400
                    )
                    
                    st.plotly_chart(fig_f, use_container_width=True)
                    st.success(f"Forecast complete. The blue line represents the predicted trend.")
                else:
                    st.error("Prediction failed. Try again later.")
            except Exception as e:
                st.error(f"Error during forecasting: {e}")

with tabs[5]:
    st.header("💰 Personal Finance Tools")
    
    f_col1, f_col2, f_col3 = st.tabs(["🔥 FIRE Calculator", "🏠 Mortgage Calculator", "⚖️ Rent vs Buy Strategy"])
    
    with f_col1:
        st.subheader("Financial Independence, Retire Early")
        c1, c2 = st.columns(2)
        with c1:
            curr_savings = st.number_input("Current Savings (PLN)", value=50000, step=5000)
            monthly_invest = st.number_input("Monthly Investment (PLN)", value=2000, step=500)
            expected_return = st.slider("Nominal Annual Return (%)", 1.0, 15.0, 7.0)
        with c2:
            monthly_expenses_retirement = st.number_input("Target Monthly Income (Today's Value)", value=5000, step=500)
            swr = st.slider("Safe Withdrawal Rate (%)", 2.0, 5.0, 4.0)
            inflation_rate = st.slider("Est. Annual Inflation (%)", 0.0, 10.0, 3.0)
            
        # 1. Calculate Target Capital in Today's Purchasing Power
        target_capital_today = (monthly_expenses_retirement * 12) / (swr / 100)
        
        # 2. Calculate Real Rate of Return (Fisher Equation approx)
        # real_r = (1 + nom) / (1 + inf) - 1
        real_annual_return = (1 + expected_return/100) / (1 + inflation_rate/100) - 1
        real_monthly_rate = (1 + real_annual_return)**(1/12) - 1
        
        # 3. Simulation (in Real Terms - purchasing power)
        months = 0
        balance_real = curr_savings
        
        while balance_real < target_capital_today and months < 1200: # max 100 years
            balance_real = (balance_real + monthly_invest) * (1 + real_monthly_rate)
            months += 1
        
        years_to_fire = months / 12
        
        # 4. Calculate Nominal Future Value for context
        # How much nominal PLN do you actually need in the future to equal target_capital_today?
        future_inflation_factor = (1 + inflation_rate/100)**years_to_fire
        target_capital_future_nominal = target_capital_today * future_inflation_factor
        future_monthly_nominal = monthly_expenses_retirement * future_inflation_factor
        
        st.divider()
        m1, m2, m3 = st.columns(3)
        m1.metric("Real Target Capital", f"{target_capital_today:,.0f} PLN", help="Amount needed in today's money")
        m2.metric("Years to FIRE", f"{years_to_fire:.1f} years", f"Real Return: {real_annual_return*100:.2f}%")
        m3.metric("Inflation Impact", f"x {future_inflation_factor:.2f}", help="How much prices will rise by then")
        
        if years_to_fire >= 100:
            st.warning("Based on these numbers (especially inflation), it's very hard to reach FIRE. Try increasing investment or return.")
        else:
            st.success(f"You will reach financial independence in **{years_to_fire:.1f} years**.")
            st.info(f"""
            **Inflation Reality Check:**
            To have the purchasing power of **{monthly_expenses_retirement:,.0f} PLN** today, in {years_to_fire:.1f} years you will need a nominal monthly income of **{future_monthly_nominal:,.0f} PLN**.
            
            Your investment portfolio will need to grow to nominally **{target_capital_future_nominal:,.0f} PLN**.
            """)

    with f_col2:
        st.subheader("Mortgage & Overpayment Simulator")
        mc1, mc2 = st.columns(2)
        with mc1:
            loan_amount = st.number_input("Loan Amount (PLN)", value=400000, step=10000)
            interest_rate = st.number_input("Annual Interest Rate (%)", value=7.5, step=0.1)
            loan_years = st.number_input("Loan Term (Years)", value=30, step=1)
        with mc2:
            overpayment = st.number_input("Monthly Overpayment (PLN)", value=0, step=100)
            
        # Standard Installment (Annuity)
        m_rate = interest_rate / 100 / 12
        n_months = loan_years * 12
        if m_rate > 0:
            standard_installment = loan_amount * (m_rate * (1 + m_rate)**n_months) / ((1 + m_rate)**n_months - 1)
        else:
            standard_installment = loan_amount / n_months
            
        # Simulation with overpayment
        total_paid = 0
        total_interest = 0
        remaining_balance = loan_amount
        actual_months = 0
        
        while remaining_balance > 0 and actual_months < 600:
            interest_part = remaining_balance * m_rate
            principal_part = standard_installment - interest_part
            
            # Apply installment + overpayment
            payment = min(remaining_balance + interest_part, standard_installment + overpayment)
            
            total_interest += interest_part
            remaining_balance -= (payment - interest_part)
            total_paid += payment
            actual_months += 1
            
        st.divider()
        mm1, mm2, mm3 = st.columns(3)
        mm1.metric("Standard Installment", f"{standard_installment:,.2f} PLN")
        mm2.metric("Actual Duration", f"{actual_months/12:.1f} years")
        mm3.metric("Total Interest", f"{total_interest:,.0f} PLN")
        
        savings_interest = (standard_installment * n_months) - total_paid
        if overpayment > 0:
            st.info(f"By overpaying **{overpayment} PLN** monthly, you save **{savings_interest:,.0f} PLN** in interest and shorten the loan by **{loan_years - actual_months/12:.1f} years**.")
        else:
            st.write(f"Total cost of loan: **{total_paid:,.0f} PLN**")

    with f_col3:
        st.subheader("Rent vs Buy: Down Payment Strategy")
        st.write("Should you buy now with a smaller down payment, or rent longer to save up?")
        
        r_col1, r_col2, r_col3 = st.columns(3)
        with r_col1:
            prop_price = st.number_input("Property Price (PLN)", value=600000, step=10000)
            curr_down_payment = st.number_input("Current Cash for Down Payment (PLN)", value=60000, step=5000)
        with r_col2:
            monthly_rent = st.number_input("Current Monthly Rent (PLN)", value=3000, step=100)
            monthly_savings_potential = st.number_input("Monthly Savings for Deposit (PLN)", value=2000, step=100)
        with r_col3:
            mortgage_rate_rb = st.number_input("Mortgage Interest Rate (%)", value=7.5, step=0.1, key="rb_rate")
            prop_appreciation = st.number_input("Est. Property Price Growth (%/year)", value=3.0, step=0.5)

        if st.button("Analyze Strategy"):
            # Simulation over 5 years
            years = list(range(1, 6))
            
            # Calculate initial loan parameters for Buy Now
            loan_now = prop_price - curr_down_payment
            r_monthly = mortgage_rate_rb / 100 / 12
            n_months_total = 30 * 12 # Assume 30 years standard
            
            # Standard payment Buy Now
            pmt_now = loan_now * (r_monthly * (1 + r_monthly)**n_months_total) / ((1 + r_monthly)**n_months_total - 1)
            
            results = []
            
            for y in years:
                months_passed = y * 12
                
                # --- SCENARIO A: BUY NOW ---
                # Future Property Value
                future_val_a = prop_price * (1 + prop_appreciation/100)**y
                
                # Remaining Balance
                # Bal = L * ((1+r)^n - (1+r)^p) / ((1+r)^n - 1)
                bal_now = loan_now * ((1 + r_monthly)**n_months_total - (1 + r_monthly)**months_passed) / ((1 + r_monthly)**n_months_total - 1)
                
                equity_buy_now = future_val_a - bal_now
                
                # --- SCENARIO B: WAIT & SAVE ---
                # You pay rent (loss), you save cash
                cash_saved = curr_down_payment + (monthly_savings_potential * months_passed)
                rent_paid = monthly_rent * months_passed
                
                # The "Gap" created by inflation
                price_increase = future_val_a - prop_price
                
                # Economic comparison
                interest_paid_approx = pmt_now * 12 * y - (loan_now - bal_now) 
                
                results.append({
                    "Year": y,
                    "Buy Now: Net Equity": equity_buy_now,
                    "Wait: Cash Savings": cash_saved,
                    "Buy Now: Interest Cost": interest_paid_approx,
                    "Wait: Rent Cost": rent_paid,
                    "Property Growth Gain": price_increase
                })
                
            df_res = pd.DataFrame(results)
            
            # Chart
            fig_rb = go.Figure()
            fig_rb.add_trace(go.Bar(x=df_res['Year'], y=df_res['Buy Now: Net Equity'], name='Net Wealth (Buy Now)', marker_color='#00C853'))
            fig_rb.add_trace(go.Bar(x=df_res['Year'], y=df_res['Wait: Cash Savings'], name='Net Wealth (Wait)', marker_color='#2962FF'))
            
            fig_rb.update_layout(title="Net Wealth Comparison", barmode='group', template="plotly_white")
            st.plotly_chart(fig_rb, use_container_width=True)
            
            # Recommendation based on Year 1
            y1 = df_res.iloc[0]
            cost_buy = y1['Buy Now: Interest Cost']
            cost_wait = y1['Wait: Rent Cost'] + y1['Property Growth Gain']
            
            diff = cost_wait - cost_buy
            
            if diff > 0:
                st.success(f"**Recommendation: BUY NOW.**")
                st.write(f"In 1 year, buying saves you **{diff:,.0f} PLN** compared to renting.")
                st.markdown(f"""
                * **Cost of Waiting:** {cost_wait:,.0f} PLN (Rent: {y1['Wait: Rent Cost']:,.0f} + Missed Growth: {y1['Property Growth Gain']:,.0f})
                * **Cost of Buying:** {cost_buy:,.0f} PLN (Interest Paid)
                """)
            else:
                st.info(f"**Recommendation: WAIT.**")
                st.write(f"In 1 year, renting is cheaper by **{abs(diff):,.0f} PLN**.")
                st.markdown(f"""
                * **Cost of Buying:** {cost_buy:,.0f} PLN (High Interest)
                * **Cost of Waiting:** {cost_wait:,.0f} PLN (Rent + Growth)
                """)
                
            with st.expander("Detailed Comparison Table"):
                st.dataframe(df_res.style.format("{:,.0f}"))

