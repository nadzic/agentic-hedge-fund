from __future__ import annotations

from dataclasses import dataclass

from app.agents.graph.schemas import Signal


@dataclass(frozen=True)
class TechnicalSnapshot:
    close: float
    rsi14: float
    macd: float
    macd_signal: float
    macd_hist: float
    ema200: float
    bb_upper: float
    bb_mid: float
    bb_lower: float


@dataclass(frozen=True)
class TechnicalDecision:
    signal: Signal
    confidence: float
    score: float
    votes_bullish: int
    votes_bearish: int
    reasoning: str
