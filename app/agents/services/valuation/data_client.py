from __future__ import annotations

from datetime import UTC, datetime

import yfinance as yf

from app.agents.services.valuation.types import ValuationSnapshot


def _safe_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _coverage(values: list[float | None]) -> float:
    if not values:
        return 0.0
    present = sum(1 for value in values if value is not None)
    return present / len(values)


def fetch_valuation_snapshot(symbol: str) -> ValuationSnapshot:
    ticker = yf.Ticker(symbol)
    info = ticker.info

    trailing_pe = _safe_float(info.get("trailingPE"))
    forward_pe = _safe_float(info.get("forwardPE"))
    peg_ratio = _safe_float(info.get("trailingPegRatio"))
    price_to_book = _safe_float(info.get("priceToBook"))
    ev_to_ebitda = _safe_float(info.get("enterpriseToEbitda"))
    market_cap = _safe_float(info.get("marketCap"))
    enterprise_value = _safe_float(info.get("enterpriseValue"))
    profit_margins = _safe_float(info.get("profitMargins"))
    return_on_equity = _safe_float(info.get("returnOnEquity"))

    coverage_values = [
        trailing_pe,
        forward_pe,
        peg_ratio,
        price_to_book,
        ev_to_ebitda,
        market_cap,
        enterprise_value,
        profit_margins,
        return_on_equity,
    ]

    return ValuationSnapshot(
        trailing_pe=trailing_pe,
        forward_pe=forward_pe,
        peg_ratio=peg_ratio,
        price_to_book=price_to_book,
        ev_to_ebitda=ev_to_ebitda,
        market_cap=market_cap,
        enterprise_value=enterprise_value,
        profit_margins=profit_margins,
        return_on_equity=return_on_equity,
        data_coverage=_coverage(coverage_values),
        as_of_date=datetime.now(UTC).date().isoformat(),
    )
