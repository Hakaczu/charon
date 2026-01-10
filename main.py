"""Charon – prosta aplikacja do pobierania kursów NBP i decyzji buy/sell/hold."""

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple, TypedDict

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template

from charon import db
from charon.decision import DecisionResult, decide_from_history
from charon.nbp_client import (
    NBPError,
    fetch_table,
    get_recent_currency_history,
    get_recent_gold_history,
)

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

app = Flask(__name__)

# Wczytaj .env jeśli istnieje
load_dotenv()

# Konfiguracja
DECISION_BIAS_PERCENT = 1.0  # próg procentowy względem średniej
HISTORY_DAYS = 60
REFRESH_SECONDS = int(os.getenv("REFRESH_SECONDS", "3600"))
PORT = int(os.getenv("PORT", "5000"))

# Zostawiamy złoto + top10 głównych walut
TOP10_CURRENCIES = [
    "USD",
    "EUR",
    "JPY",
    "GBP",
    "AUD",
    "CAD",
    "CHF",
    "CNY",
    "SEK",
    "NZD",
    "NOK",
]

# Ikony CSS (klasy) dla walut; fallback na generic
CURRENCY_ICON_CLASS = {
    "USD": "fa-solid fa-dollar-sign",
    "EUR": "fa-solid fa-euro-sign",
    "JPY": "fa-solid fa-yen-sign",
    "GBP": "fa-solid fa-sterling-sign",
    "AUD": "fa-solid fa-dollar-sign",
    "CAD": "fa-solid fa-dollar-sign",
    "CHF": "fa-solid fa-coins",
    "CNY": "fa-solid fa-coins",
    "SEK": "fa-solid fa-coins",
    "NZD": "fa-solid fa-dollar-sign",
    "NOK": "fa-solid fa-coins",
    "XAU": "fa-solid fa-gem",
}

class CacheStore(TypedDict):
    items: List[DecisionResult]
    last_fetch: Optional[datetime]


# Cache danych, aby nie pobierać z NBP przy każdym odświeżeniu strony
_CACHE: CacheStore = {
    "items": [],
    "last_fetch": None,
}

# Inicjalizacja bazy przy starcie aplikacji
db.init_db()


def _decorate_decision(decision: DecisionResult, code: str, name: str) -> DecisionResult:
    decision.code = code
    decision.name = name
    decision.icon_class = CURRENCY_ICON_CLASS.get(code.upper(), "fa-solid fa-coins")
    return decision


def _build_instruments() -> Tuple[List[DecisionResult], datetime]:
    """Pobiera top waluty z tabeli A + złoto, zapisuje do DB, zwraca decyzje."""
    instruments: List[DecisionResult] = []
    table = fetch_table("A")
    table_map = {item["code"]: item for item in table}
    codes = [code for code in TOP10_CURRENCIES if code in table_map]

    with db.get_session() as session:
        for code in codes:
            history = get_recent_currency_history(code, days=HISTORY_DAYS)
            decision = decide_from_history(history, bias=DECISION_BIAS_PERCENT)
            name = table_map.get(code, {}).get("currency", code)

            # zapisz historię do bazy (bez duplikatów)
            db.save_currency_history(session, code=code, name=name, history=history)
            instruments.append(_decorate_decision(decision, code=code, name=name))

        gold_history = get_recent_gold_history(days=HISTORY_DAYS)
        db.save_gold_history(session, history=gold_history)

    gold_decision = decide_from_history(gold_history, bias=DECISION_BIAS_PERCENT)
    instruments.append(_decorate_decision(gold_decision, code="XAU", name="Złoto (1g)"))

    fetched_at = datetime.now(timezone.utc)
    return instruments, fetched_at


def _ensure_cached_data() -> Tuple[List[DecisionResult], Optional[datetime], Optional[datetime]]:
    now = datetime.now(timezone.utc)
    last_fetch: Optional[datetime] = _CACHE["last_fetch"]
    needs_refresh = last_fetch is None or (now - last_fetch) >= timedelta(seconds=REFRESH_SECONDS)

    if needs_refresh:
        instruments, fetched_at = _build_instruments()
        _CACHE["items"] = instruments
        _CACHE["last_fetch"] = fetched_at
        last_fetch = fetched_at

    next_refresh = last_fetch + timedelta(seconds=REFRESH_SECONDS) if last_fetch else None
    return _CACHE.get("items", []), last_fetch, next_refresh


def _fmt_ts(ts: Optional[datetime]) -> str:
    if not ts:
        return "—"
    return ts.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


@app.route("/")
def index():
    try:
        instruments, last_fetch, next_refresh = _ensure_cached_data()
        return render_template(
            "index.html",
            items=instruments,
            last_fetch=_fmt_ts(last_fetch),
            next_refresh=_fmt_ts(next_refresh),
            refresh_seconds=REFRESH_SECONDS,
        )
    except Exception as exc:  # pragma: no cover - UI fallback
        logging.exception("Błąd podczas budowy widoku")
        return f"Wystąpił błąd: {exc}", 500


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.errorhandler(NBPError)
def handle_nbp_error(error: NBPError):
    return jsonify({"error": str(error)}), 502


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=PORT)