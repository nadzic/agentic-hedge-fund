from __future__ import annotations

from app.agents.services.sentiment.news_client import fetch_sentiment_texts
from app.agents.services.sentiment.scoring import (
    SentimentDecision,
    build_sentiment_snapshot_from_texts,
    score_sentiment,
)


def run_sentiment_analysis(
    symbol: str,
    horizon: str,
    query: str,
) -> tuple[SentimentDecision, dict[str, float | int | str]]:
    lookback_days = 7
    max_news_items = 20

    texts, source, news_count = fetch_sentiment_texts(
        symbol=symbol,
        query=query,
        lookback_days=lookback_days,
        max_news_items=max_news_items,
    )
    snapshot = build_sentiment_snapshot_from_texts(texts)
    decision = score_sentiment(snapshot)

    metrics: dict[str, float | int | str] = {
        "bullish_hits": snapshot.bullish_hits,
        "bearish_hits": snapshot.bearish_hits,
        "neutral_hits": snapshot.neutral_hits,
        "sentiment_score": decision.score,
        "confidence_base": snapshot.confidence_base,
        "source_count": len(texts),
        "news_count": news_count,
        "window_days": lookback_days,
        "horizon": horizon,
        "data_source": source,
    }
    return decision, metrics