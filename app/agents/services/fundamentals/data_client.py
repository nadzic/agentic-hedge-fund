from __future__ import annotations

from datetime import UTC, datetime

import yfinance as yf

from app.agents.services.fundamentals.types import FundamentalSnapshot


def _safe_float(value: str | int | float | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coverage(values: list[float | None]) -> float:
    if not values:
        return 0.0
    present = sum(1 for value in values if value is not None)
    return present / len(values)


def fetch_fundamental_snapshot(symbol: str) -> FundamentalSnapshot:
    ticker = yf.Ticker(symbol)
    info = ticker.info

    revenue_growth = _safe_float(info.get("revenueGrowth"))
    earnings_growth = _safe_float(info.get("earningsGrowth"))
    gross_margin = _safe_float(info.get("grossMargins"))
    operating_margin = _safe_float(info.get("operatingMargins"))
    debt_to_equity = _safe_float(info.get("debtToEquity"))
    current_ratio = _safe_float(info.get("currentRatio"))
    roe = _safe_float(info.get("returnOnEquity"))

    trailing_pe = _safe_float(info.get("trailingPE"))
    forward_pe = _safe_float(info.get("forwardPE"))
    pe_ratio = trailing_pe if trailing_pe is not None else forward_pe

    free_cashflow = _safe_float(info.get("freeCashflow"))
    total_revenue = _safe_float(info.get("totalRevenue"))
    fcf_margin = None
    if free_cashflow is not None and total_revenue is not None and total_revenue != 0:
        fcf_margin = free_cashflow / total_revenue

    values_for_coverage = [
        revenue_growth,
        earnings_growth,
        gross_margin,
        operating_margin,
        fcf_margin,
        debt_to_equity,
        current_ratio,
        roe,
        pe_ratio,
    ]

    return FundamentalSnapshot(
        revenue_growth=revenue_growth,
        earnings_growth=earnings_growth,
        gross_margin=gross_margin,
        operating_margin=operating_margin,
        fcf_margin=fcf_margin,
        debt_to_equity=debt_to_equity,
        current_ratio=current_ratio,
        roe=roe,
        pe_ratio=pe_ratio,
        data_coverage=_coverage(values_for_coverage),
        as_of_date=datetime.now(UTC).date().isoformat(),
    )
