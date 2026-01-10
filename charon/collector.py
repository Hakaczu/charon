"""Module responsible for collecting data from NBP and persisting it.

This module encapsulates fetching currency/gold histories, saving them to DB
and producing decision objects. It keeps its own logger and log file.
"""
from __future__ import annotations

import logging
import os
from dataclasses import asdict
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from typing import List, Optional, Tuple

from . import db
from .constants import CURRENCY_ICON_CLASS, TOP10_CURRENCIES
from .decision import DecisionResult, decide_from_history
from .nbp_client import (
    fetch_table,
    get_recent_currency_history,
    get_recent_gold_history,
)


LOGGER_NAME = os.getenv("COLLECTOR_LOGGER_NAME", "charon.collector")
LOG_FILE = os.getenv("COLLECTOR_LOG_FILE", "collector.log")


def _get_logger() -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    # Re-read env so tests can set COLLECTOR_LOG_FILE before import
    log_file = os.getenv("COLLECTOR_LOG_FILE", LOG_FILE)
    has_file = False
    for h in logger.handlers:
        if isinstance(h, RotatingFileHandler) and getattr(h, "baseFilename", None) == log_file:
            has_file = True
            break

    if not has_file:
        formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
        handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


def collect(codes: Optional[List[str]] = None, days: int = 60) -> Tuple[List[DecisionResult], datetime]:
    """Collect data for given codes (or TOP10) and persist to DB.

    Returns (decisions, fetched_at).
    """
    logger = _get_logger()
    fetched_at = datetime.now(timezone.utc)
    table = fetch_table("A")
    table_map = {item["code"]: item for item in table}
    selected = codes or TOP10_CURRENCIES

    decisions: List[DecisionResult] = []
    inserted_total = 0

    with db.get_session() as session:
        for code in selected:
            name = table_map.get(code, {}).get("currency", code)
            try:
                history = get_recent_currency_history(code, days)
            except Exception:
                logger.exception("Failed to fetch history for %s", code)
                continue

            if not history:
                logger.warning("No history for %s - skipping", code)
                continue

            try:
                decision = decide_from_history(history)
            except Exception:
                logger.exception("Decision calculation failed for %s", code)
                continue

            # fill metadata
            decision.code = code
            decision.name = name

            try:
                inserted = db.save_currency_history(session, code=code, name=name, history=history)
                inserted_total += inserted
            except Exception:
                logger.exception("DB save failed for %s", code)
                continue

            decision = _attach_icon(decision, code)
            decisions.append(decision)
            logger.info("%s: fetched %d points, inserted %d rows", code, len(history), inserted)

        # Gold
        try:
            gold_history = get_recent_gold_history(days)
        except Exception:
            logger.exception("Failed to fetch gold history")
            gold_history = []

        if gold_history:
            try:
                inserted = db.save_gold_history(session, history=gold_history)
                inserted_total += inserted
                gold_decision = decide_from_history(gold_history)
                gold_decision.code = "XAU"
                gold_decision.name = "Złoto (1g)"
                gold_decision = _attach_icon(gold_decision, "XAU")
                decisions.append(gold_decision)
                logger.info("Gold: fetched %d points, inserted %d rows", len(gold_history), inserted)
            except Exception:
                logger.exception("DB save failed for gold")

    logger.info("Collect finished: %d instruments, %d rows inserted", len(decisions), inserted_total)
    return decisions, fetched_at


def _attach_icon(decision: DecisionResult, code: str) -> DecisionResult:
    decision.icon_class = CURRENCY_ICON_CLASS.get(code.upper(), "fa-solid fa-coins")
    return decision
