import os
from datetime import date, timedelta

import httpx
import pandas as pd
import streamlit as st

API_BASE = os.getenv("API_BASE", "http://api:8000")
TOP_CODES = ["USD", "EUR", "CHF", "GBP", "JPY", "AUD", "CAD", "NOK"]
LOOKBACK_DAYS = 365  # pokaż maksymalny roczny zakres


@st.cache_data(ttl=300)
def fetch(path: str, params=None):
    url = f"{API_BASE}{path}"
    r = httpx.get(url, params=params, timeout=15.0)
    r.raise_for_status()
    return r.json()


def load_rates(code: str):
    to_d = date.today()
    from_d = to_d - timedelta(days=LOOKBACK_DAYS)
    data = fetch("/rates", {"code": code, "from_date": from_d, "to_date": to_d})
    df = pd.DataFrame(data)
    if df.empty:
        return df
    df["effective_date"] = pd.to_datetime(df["effective_date"])
    return df.sort_values("effective_date")


def load_signals(code: str, limit: int = 10):
    sigs = fetch("/signals", {"code": code, "limit": limit})
    return pd.DataFrame(sigs)


def latest_value(df: pd.DataFrame):
    if df.empty:
        return None
    return float(df.iloc[-1]["rate_mid"])


st.set_page_config(page_title="Charon Dashboard", layout="wide")
st.title("Charon – kursy NBP, złoto, sygnały (multi-asset)")
st.caption("Wszystkie najważniejsze waluty + złoto na jednym ekranie. Dane z NBP, sygnały z MACD.")

# GOLD SECTION
gold_df = pd.DataFrame(
    fetch(
        "/gold",
        {
            "from_date": date.today() - timedelta(days=365),
            "to_date": date.today(),
        },
    )
)
if not gold_df.empty:
    gold_df["effective_date"] = pd.to_datetime(gold_df["effective_date"])
    gold_last = float(gold_df.iloc[-1]["price"])
    gold_prev = float(gold_df.iloc[-2]["price"]) if len(gold_df) > 1 else gold_last
    gold_change = gold_last - gold_prev
else:
    gold_last, gold_change = None, None

metrics_cols = st.columns(4)

# Gold metric
with metrics_cols[0]:
    if gold_last is None:
        st.metric("Złoto (PLN/oz)", "brak danych")
    else:
        st.metric("Złoto (PLN/oz)", f"{gold_last:,.2f}", f"{gold_change:+.2f} d/d")

# First few currency metrics
for idx, code in enumerate(TOP_CODES[:3], start=1):
    df = load_rates(code)
    val = latest_value(df)
    prev = float(df.iloc[-2]["rate_mid"]) if len(df) > 1 else val
    change = val - prev if val is not None else None
    with metrics_cols[idx]:
        if val is None:
            st.metric(f"{code}/PLN", "brak")
        else:
            st.metric(f"{code}/PLN", f"{val:,.4f}", f"{change:+.4f} d/d")

st.markdown("---")

# Charts grid with indicators to the side
summary_rows = []
cols = st.columns(2)
for i, code in enumerate(TOP_CODES):
    df = load_rates(code)
    sigs = load_signals(code, limit=5)
    target_col = cols[i % 2]
    with target_col:
        st.markdown(f"### {code} / PLN")
        if df.empty:
            st.warning("Brak danych")
            continue
        chart_col, info_col = st.columns((3, 1))
        chart_col.line_chart(df.set_index("effective_date")["rate_mid"], height=180, use_container_width=True)
        last_price = df.iloc[-1]["rate_mid"]
        prev_price = df.iloc[-2]["rate_mid"] if len(df) > 1 else last_price
        change = last_price - prev_price
        last_sig = sigs.iloc[0] if not sigs.empty else None
        with info_col:
            st.metric("Kurs", f"{last_price:,.4f}", f"{change:+.4f} d/d")
            if last_sig is not None:
                st.metric("Sygnał", last_sig["signal"], f"MACD {last_sig['macd']:.4f}")
            else:
                st.caption("Brak sygnału")
        # zbierz do tabeli podsumowania
        summary_rows.append(
            {
                "asset": code,
                "last_price": round(float(last_price), 4),
                "change_d": round(float(change), 4),
                "signal": last_sig["signal"] if last_sig is not None else "HOLD",
                "macd": round(float(last_sig["macd"]), 4) if last_sig is not None else None,
                "hist": round(float(last_sig["histogram"]), 4) if last_sig is not None else None,
                "updated": df.iloc[-1]["effective_date"],
            }
        )

# Gold chart
st.markdown("---")
st.subheader("Złoto (PLN)")
if gold_df.empty:
    st.warning("Brak danych złota")
else:
    st.line_chart(gold_df.set_index("effective_date")["price"], height=240)
    gold_sig = load_signals("GOLD", limit=5)
    if not gold_sig.empty:
        st.caption("Sygnały złota")
        st.dataframe(gold_sig[["generated_at", "signal", "macd", "signal_line", "histogram"]], use_container_width=True)
    # dodaj do tabeli
    summary_rows.append(
        {
            "asset": "GOLD",
            "last_price": round(float(gold_last), 2),
            "change_d": round(float(gold_change), 2) if gold_change is not None else None,
            "signal": gold_sig.iloc[0]["signal"] if not gold_sig.empty else "HOLD",
            "macd": round(float(gold_sig.iloc[0]["macd"]), 4) if not gold_sig.empty else None,
            "hist": round(float(gold_sig.iloc[0]["histogram"]), 4) if not gold_sig.empty else None,
            "updated": gold_df.iloc[-1]["effective_date"] if not gold_df.empty else None,
        }
    )

# Miner stats
st.markdown("---")
st.subheader("Miner / zadania")
stats = fetch("/stats/miner")
cols_stats = st.columns(3)
cols_stats[0].metric("Joby ogółem", stats.get("total_jobs", 0))
cols_stats[1].metric("Sukcesy", stats.get("success_jobs", 0))
cols_stats[2].metric("Niepowodzenia", stats.get("failed_jobs", 0))
st.dataframe(pd.DataFrame(stats.get("last_jobs", [])), use_container_width=True)

# Summary decision table
st.markdown("---")
st.subheader("Tabela decyzji (ostatni sygnał)")
if summary_rows:
    sum_df = pd.DataFrame(summary_rows)
    st.dataframe(sum_df, use_container_width=True)
else:
    st.info("Brak danych do podsumowania.")
