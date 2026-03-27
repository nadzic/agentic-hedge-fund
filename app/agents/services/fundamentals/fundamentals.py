from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import yfinance as yf
from app.agents.graph.schemas import Signal


@dataclass(frozen=True)
class FundamentalSnapshot:
    revenue_growth: float | None
    earnings_growth: float | None
    gross_margin: float | None
    operating_margin: float | None
    fcf_margin: float | None
    debt_to_equity: float | None
    current_ratio: float | None
    roe: float | None
    pe_ratio: float | None
    data_coverage: float
    as_of_date: str


@dataclass(frozen=True)
class FundamentalDecision:
    signal: Signal
    confidence: float
    score: float
    reasoning: str


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
    if (
        free_cashflow is not None
        and total_revenue is not None
        and total_revenue != 0
    ):
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
        as_of_date=datetime.now(timezone.utc).date().isoformat(),
    )


def _score_metric(value: float | None, bullish_if_gt: float, bearish_if_lt: float) -> int:
    if value is None:
        return 0
    if value > bullish_if_gt:
        return 1
    if value < bearish_if_lt:
        return -1
    return 0


def score_fundamentals(snapshot: FundamentalSnapshot) -> FundamentalDecision:
    votes: list[tuple[str, int]] = []
    votes.append(
        (
            "revenue_growth",
            _score_metric(snapshot.revenue_growth, bullish_if_gt=0.08, bearish_if_lt=0.0),
        )
    )
    votes.append(
        (
            "earnings_growth",
            _score_metric(snapshot.earnings_growth, bullish_if_gt=0.10, bearish_if_lt=0.0),
        )
    )
    votes.append(
        (
            "gross_margin",
            _score_metric(snapshot.gross_margin, bullish_if_gt=0.35, bearish_if_lt=0.15),
        )
    )
    votes.append(
        (
            "operating_margin",
            _score_metric(snapshot.operating_margin, bullish_if_gt=0.12, bearish_if_lt=0.05),
        )
    )
    votes.append(
        (
            "fcf_margin",
            _score_metric(snapshot.fcf_margin, bullish_if_gt=0.08, bearish_if_lt=0.0),
        )
    )
    votes.append(
        (
            "roe",
            _score_metric(snapshot.roe, bullish_if_gt=0.12, bearish_if_lt=0.05),
        )
    )
    # Reverse thresholds for debt_to_equity: lower is better.
    debt_vote = 0
    if snapshot.debt_to_equity is not None:
        if snapshot.debt_to_equity < 1.0:
            debt_vote = 1
        elif snapshot.debt_to_equity > 2.0:
            debt_vote = -1
    votes.append(("debt_to_equity", debt_vote))
    # Current ratio: too low is weak liquidity.
    current_ratio_vote = 0
    if snapshot.current_ratio is not None:
        if snapshot.current_ratio > 1.2:
            current_ratio_vote = 1
        elif snapshot.current_ratio < 0.9:
            current_ratio_vote = -1
    votes.append(("current_ratio", current_ratio_vote))
    # Valuation sanity check.
    pe_vote = 0
    if snapshot.pe_ratio is not None:
        if 10 <= snapshot.pe_ratio <= 30:
            pe_vote = 1
        elif snapshot.pe_ratio > 45:
            pe_vote = -1
    votes.append(("pe_ratio", pe_vote))
    total_points = sum(vote for _, vote in votes)
    score = total_points / len(votes)  # normalized [-1, 1]
    if score >= 0.30:
        signal = Signal.BUY
    elif score <= -0.30:
        signal = Signal.SELL
    else:
        signal = Signal.HOLD
    # Confidence grows with score magnitude and data coverage.
    base_conf = 0.50 + abs(score) * 0.35
    coverage_adj = 0.15 * snapshot.data_coverage
    confidence = max(0.50, min(0.92, base_conf + coverage_adj))
    vote_text = ", ".join(f"{name}:{vote:+d}" for name, vote in votes)
    reasoning = (
        f"Fundamental score={score:.2f}, coverage={snapshot.data_coverage:.2f}, votes=[{vote_text}]"
    )
    return FundamentalDecision(
        signal=signal,
        confidence=confidence,
        score=score,
        reasoning=reasoning,
    )


def run_fundamentals_analysis(
    symbol: str, horizon: str
) -> tuple[FundamentalDecision, dict[str, float | int | str]]:
    # horizon kept for interface parity with other analysts
    _ = horizon
    snapshot = fetch_fundamental_snapshot(symbol)
    decision = score_fundamentals(snapshot)
    metrics: dict[str, float | int | str] = {
        "revenue_growth": snapshot.revenue_growth if snapshot.revenue_growth is not None else "na",
        "earnings_growth": snapshot.earnings_growth if snapshot.earnings_growth is not None else "na",
        "gross_margin": snapshot.gross_margin if snapshot.gross_margin is not None else "na",
        "operating_margin": snapshot.operating_margin if snapshot.operating_margin is not None else "na",
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