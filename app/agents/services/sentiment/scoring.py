from __future__ import annotations

from dataclasses import dataclass

from app.agents.graph.schemas import Signal
from app.agents.services.sentiment.constants import (
    BEARISH_KEYWORDS,
    BULLISH_KEYWORDS,
    NEUTRAL_KEYWORDS,
)


@dataclass(frozen=True)
class SentimentSnapshot:
    bullish_hits: int
    bearish_hits: int
    neutral_hits: int
    net_score: float
    confidence_base: float


@dataclass(frozen=True)
class SentimentDecision:
    signal: Signal
    confidence: float
    score: float
    reasoning: str


def _count_hits(text: str, keywords: tuple[str, ...]) -> int:
    lower_text = text.lower()
    return sum(1 for keyword in keywords if keyword in lower_text)


def build_sentiment_snapshot_from_texts(texts: list[str]) -> SentimentSnapshot:
    bullish_hits = sum(_count_hits(text, BULLISH_KEYWORDS) for text in texts)
    bearish_hits = sum(_count_hits(text, BEARISH_KEYWORDS) for text in texts)
    neutral_hits = sum(_count_hits(text, NEUTRAL_KEYWORDS) for text in texts)

    total_directional = bullish_hits + bearish_hits
    net_score = 0.0 if total_directional == 0 else (bullish_hits - bearish_hits) / total_directional
    confidence_base = 0.50 + min(0.30, 0.02 * total_directional)

    return SentimentSnapshot(
        bullish_hits=bullish_hits,
        bearish_hits=bearish_hits,
        neutral_hits=neutral_hits,
        net_score=net_score,
        confidence_base=confidence_base,
    )


def score_sentiment(snapshot: SentimentSnapshot) -> SentimentDecision:
    if snapshot.net_score >= 0.35:
        signal = Signal.BUY
    elif snapshot.net_score <= -0.35:
        signal = Signal.SELL
    else:
        signal = Signal.HOLD

    confidence = max(0.50, min(0.90, snapshot.confidence_base + abs(snapshot.net_score) * 0.20))

    reasoning = (
        f"Sentiment score={snapshot.net_score:.2f}, "
        f"bullish_hits={snapshot.bullish_hits}, "
        f"bearish_hits={snapshot.bearish_hits}, "
        f"neutral_hits={snapshot.neutral_hits}."
    )
    return SentimentDecision(
        signal=signal,
        confidence=confidence,
        score=snapshot.net_score,
        reasoning=reasoning,
    )
