from __future__ import annotations

from dataclasses import dataclass

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
