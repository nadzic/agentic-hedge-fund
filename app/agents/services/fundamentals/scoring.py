from __future__ import annotations

from app.agents.graph.schemas import Signal
from app.agents.services.fundamentals.types import FundamentalDecision, FundamentalSnapshot


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

    debt_vote = 0
    if snapshot.debt_to_equity is not None:
        if snapshot.debt_to_equity < 1.0:
            debt_vote = 1
        elif snapshot.debt_to_equity > 2.0:
            debt_vote = -1
    votes.append(("debt_to_equity", debt_vote))

    current_ratio_vote = 0
    if snapshot.current_ratio is not None:
        if snapshot.current_ratio > 1.2:
            current_ratio_vote = 1
        elif snapshot.current_ratio < 0.9:
            current_ratio_vote = -1
    votes.append(("current_ratio", current_ratio_vote))

    pe_vote = 0
    if snapshot.pe_ratio is not None:
        if 10 <= snapshot.pe_ratio <= 30:
            pe_vote = 1
        elif snapshot.pe_ratio > 45:
            pe_vote = -1
    votes.append(("pe_ratio", pe_vote))

    total_points = sum(vote for _, vote in votes)
    score = total_points / len(votes)

    if score >= 0.30:
        signal = Signal.BUY
    elif score <= -0.30:
        signal = Signal.SELL
    else:
        signal = Signal.HOLD

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
