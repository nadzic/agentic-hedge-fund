from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InsiderSnapshot:
    buy_count: int
    sell_count: int
    buy_shares: float
    sell_shares: float
    buy_value_used: float
    sell_value_used: float
    net_shares: float
    net_value_used: float
    buy_value_usd: float
    sell_value_usd: float
    net_value_usd: float


@dataclass(frozen=True)
class InsiderDecision:
    score: float
    confidence: float
    reasoning: str