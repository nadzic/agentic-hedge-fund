from __future__ import annotations

from app.agents.services.fundamentals.data_client import fetch_fundamental_snapshot
from app.agents.services.fundamentals.scoring import FundamentalDecision, score_fundamentals


def run_fundamentals_analysis(
    symbol: str, horizon: str
) -> tuple[FundamentalDecision, dict[str, float | int | str]]:
    # horizon kept for interface parity with other analysts
    _ = horizon
    snapshot = fetch_fundamental_snapshot(symbol)
    decision = score_fundamentals(snapshot)
    earnings_growth = snapshot.earnings_growth if snapshot.earnings_growth is not None else "na"
    operating_margin = snapshot.operating_margin if snapshot.operating_margin is not None else "na"
    metrics: dict[str, float | int | str] = {
        "revenue_growth": snapshot.revenue_growth if snapshot.revenue_growth is not None else "na",
        "earnings_growth": earnings_growth,
        "gross_margin": snapshot.gross_margin if snapshot.gross_margin is not None else "na",
        "operating_margin": operating_margin,
        "fcf_margin": snapshot.fcf_margin if snapshot.fcf_margin is not None else "na",
        "debt_to_equity": snapshot.debt_to_equity if snapshot.debt_to_equity is not None else "na",
        "current_ratio": snapshot.current_ratio if snapshot.current_ratio is not None else "na",
        "roe": snapshot.roe if snapshot.roe is not None else "na",
        "pe_ratio": snapshot.pe_ratio if snapshot.pe_ratio is not None else "na",
        "fundamental_score": decision.score,
        "data_coverage": snapshot.data_coverage,
        "as_of_date": snapshot.as_of_date,
        "data_source": "yfinance",
    }
    return decision, metrics