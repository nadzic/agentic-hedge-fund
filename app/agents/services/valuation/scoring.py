from __future__ import annotations

from app.agents.graph.schemas import Signal
from app.agents.services.valuation.types import ValuationDecision, ValuationSnapshot


def _score_range(value: float | None, bullish_max: float, bearish_min: float) -> int:
    if value is None:
        return 0
    if value <= bullish_max:
        return 1
    if value >= bearish_min:
        return -1
    return 0


def score_valuation(snapshot: ValuationSnapshot) -> ValuationDecision:
    votes: list[tuple[str, int]] = []

    pe_ref = snapshot.forward_pe if snapshot.forward_pe is not None else snapshot.trailing_pe
    votes.append(("pe_ratio", _score_range(pe_ref, bullish_max=25.0, bearish_min=45.0)))
    votes.append(("peg_ratio", _score_range(snapshot.peg_ratio, bullish_max=1.5, bearish_min=3.0)))
    votes.append(
        ("price_to_book", _score_range(snapshot.price_to_book, bullish_max=4.0, bearish_min=8.0))
    )
    votes.append(
        ("ev_to_ebitda", _score_range(snapshot.ev_to_ebitda, bullish_max=15.0, bearish_min=30.0))
    )

    margin_vote = 0
    if snapshot.profit_margins is not None:
        if snapshot.profit_margins >= 0.15:
            margin_vote = 1
        elif snapshot.profit_margins <= 0.05:
            margin_vote = -1
    votes.append(("profit_margins", margin_vote))

    roe_vote = 0
    if snapshot.return_on_equity is not None:
        if snapshot.return_on_equity >= 0.12:
            roe_vote = 1
        elif snapshot.return_on_equity <= 0.05:
            roe_vote = -1
    votes.append(("return_on_equity", roe_vote))

    total_points = sum(vote for _, vote in votes)
    score = total_points / len(votes)

    if score >= 0.30:
        signal = Signal.BUY
    elif score <= -0.30:
        signal = Signal.SELL
    else:
        signal = Signal.HOLD

    base_conf = 0.50 + abs(score) * 0.30
    coverage_adj = 0.15 * snapshot.data_coverage
    confidence = max(0.50, min(0.92, base_conf + coverage_adj))

    vote_text = ", ".join(f"{name}:{vote:+d}" for name, vote in votes)
    reasoning = (
        f"Valuation score={score:.2f}, coverage={snapshot.data_coverage:.2f}, "
        f"votes=[{vote_text}]"
    )

    return ValuationDecision(
        signal=signal,
        confidence=confidence,
        score=score,
        reasoning=reasoning,
    )
