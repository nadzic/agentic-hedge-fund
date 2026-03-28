from __future__ import annotations

from dataclasses import dataclass

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
