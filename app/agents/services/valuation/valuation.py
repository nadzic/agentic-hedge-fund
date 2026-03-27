from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import yfinance as yf

from app.agents.graph.schemas import Signal


@dataclass(frozen=True)
class ValuationSnapshot:
    trailing_pe: float | None
    forward_pe: float | None
    peg_ratio: float | None
    price_to_book: float | None
    ev_to_ebitda: float | None
    market_cap: float | None
    enterprise_value: float | None
    profit_margins: float | None
    return_on_equity: float | None
    data_coverage: float
    as_of_date: str


@dataclass(frozen=True)
class ValuationDecision:
    signal: Signal
    confidence: float
    score: float
    reasoning: str


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
        as_of_date=datetime.now(timezone.utc).date().isoformat(),
    )


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
    votes.append(("price_to_book", _score_range(snapshot.price_to_book, bullish_max=4.0, bearish_min=8.0)))
    votes.append(("ev_to_ebitda", _score_range(snapshot.ev_to_ebitda, bullish_max=15.0, bearish_min=30.0)))

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
    score = total_points / len(votes)  # normalized [-1, 1]

    if score >= 0.30:
        signal = Signal.BUY
    elif score <= -0.30:
        signal = Signal.SELL
    else:
        signal = Signal.HOLD

    # Confidence grows with signal strength + data coverage.
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


def run_valuation_analysis(
    symbol: str,
    horizon: str,
) -> tuple[ValuationDecision, dict[str, float | int | str]]:
    # Keep interface parity with other analysts.
    _ = horizon
    snapshot = fetch_valuation_snapshot(symbol)
    decision = score_valuation(snapshot)

    metrics: dict[str, float | int | str] = {
        "trailing_pe": snapshot.trailing_pe if snapshot.trailing_pe is not None else "na",
        "forward_pe": snapshot.forward_pe if snapshot.forward_pe is not None else "na",
        "peg_ratio": snapshot.peg_ratio if snapshot.peg_ratio is not None else "na",
        "price_to_book": snapshot.price_to_book if snapshot.price_to_book is not None else "na",
        "ev_to_ebitda": snapshot.ev_to_ebitda if snapshot.ev_to_ebitda is not None else "na",
        "market_cap": snapshot.market_cap if snapshot.market_cap is not None else "na",
        "enterprise_value": snapshot.enterprise_value if snapshot.enterprise_value is not None else "na",
        "profit_margins": snapshot.profit_margins if snapshot.profit_margins is not None else "na",
        "return_on_equity": snapshot.return_on_equity if snapshot.return_on_equity is not None else "na",
        "valuation_score": decision.score,
        "data_coverage": snapshot.data_coverage,
        "as_of_date": snapshot.as_of_date,
        "data_source": "yfinance",
    }

    return decision, metrics