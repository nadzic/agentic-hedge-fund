from __future__ import annotations

from app.agents.services.valuation.data_client import fetch_valuation_snapshot
from app.agents.services.valuation.scoring import ValuationDecision, score_valuation


def run_valuation_analysis(
    symbol: str,
    horizon: str,
) -> tuple[ValuationDecision, dict[str, float | int | str]]:
    # Keep interface parity with other analysts.
    _ = horizon
    snapshot = fetch_valuation_snapshot(symbol)
    decision = score_valuation(snapshot)
    enterprise_value = snapshot.enterprise_value if snapshot.enterprise_value is not None else "na"
    return_on_equity = snapshot.return_on_equity if snapshot.return_on_equity is not None else "na"

    metrics: dict[str, float | int | str] = {
        "trailing_pe": snapshot.trailing_pe if snapshot.trailing_pe is not None else "na",
        "forward_pe": snapshot.forward_pe if snapshot.forward_pe is not None else "na",
        "peg_ratio": snapshot.peg_ratio if snapshot.peg_ratio is not None else "na",
        "price_to_book": snapshot.price_to_book if snapshot.price_to_book is not None else "na",
        "ev_to_ebitda": snapshot.ev_to_ebitda if snapshot.ev_to_ebitda is not None else "na",
        "market_cap": snapshot.market_cap if snapshot.market_cap is not None else "na",
        "enterprise_value": enterprise_value,
        "profit_margins": snapshot.profit_margins if snapshot.profit_margins is not None else "na",
        "return_on_equity": return_on_equity,
        "valuation_score": decision.score,
        "data_coverage": snapshot.data_coverage,
        "as_of_date": snapshot.as_of_date,
        "data_source": "yfinance",
    }

    return decision, metrics