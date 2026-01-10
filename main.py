"""Charon – prosta aplikacja do pobierania kursów NBP i decyzji buy/sell/hold."""

import logging
import os
from typing import List
CURRENCIES = ["USD", "EUR", "CHF", "GBP"]
DECISION_BIAS_PERCENT = 1.0  # próg procentowy względem średniej
HISTORY_DAYS = 60
PORT = int(os.getenv("PORT", "5000"))

from flask import Flask, jsonify, render_template

from charon.decision import DecisionResult, decide_from_history
from charon.nbp_client import (
	NBPError,
	fetch_table,
	get_recent_currency_history,
	get_recent_gold_history,
)

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

app = Flask(__name__)

# Konfiguracja
CURRENCIES = ["USD", "EUR", "CHF", "GBP"]
DECISION_BIAS_PERCENT = 1.0  # próg procentowy względem średniej
HISTORY_DAYS = 60


def _decorate_decision(decision: DecisionResult, code: str, name: str) -> DecisionResult:
	decision.code = code
	decision.name = name
	return decision


def build_instruments() -> List[DecisionResult]:
	instruments: List[DecisionResult] = []
	table = fetch_table("A")
	table_map = {item["code"]: item for item in table}

	for code in CURRENCIES:
		history = get_recent_currency_history(code, days=HISTORY_DAYS)
		decision = decide_from_history(history, bias=DECISION_BIAS_PERCENT)
		name = table_map.get(code, {}).get("currency", code)
		instruments.append(_decorate_decision(decision, code=code, name=name))

	gold_history = get_recent_gold_history(days=HISTORY_DAYS)
	gold_decision = decide_from_history(gold_history, bias=DECISION_BIAS_PERCENT)
	instruments.append(_decorate_decision(gold_decision, code="XAU", name="Złoto (1g)"))

	return instruments


@app.route("/")
def index():
	try:
		instruments = build_instruments()
		return render_template("index.html", items=instruments)
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