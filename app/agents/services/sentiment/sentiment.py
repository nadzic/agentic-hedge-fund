from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import os
import httpx
import yfinance as yf
from app.agents.graph.schemas import Signal

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
BULLISH_KEYWORDS: tuple[str, ...] = (
    "beat",
    "upgrade",
    "bullish",
    "buy",
    "outperform",
    "momentum",
    "breakout",
    "strong demand",
    "guidance raised",
    "record revenue",
    "raised target",
)
BEARISH_KEYWORDS: tuple[str, ...] = (
    "miss",
    "downgrade",
    "bearish",
    "sell",
    "underperform",
    "weak demand",
    "guidance cut",
    "risk-off",
    "decline",
    "lawsuit",
    "investigation",
)
NEUTRAL_KEYWORDS: tuple[str, ...] = (
    "mixed",
    "uncertain",
    "sideways",
    "range-bound",
    "wait",
    "hold",
    "flat",
    "unchanged",
)
def _count_hits(text: str, keywords: tuple[str, ...]) -> int:
    lower = text.lower()
    return sum(1 for keyword in keywords if keyword in lower)
def _build_sentiment_snapshot_from_texts(texts: list[str]) -> SentimentSnapshot:
    bullish_hits = sum(_count_hits(text, BULLISH_KEYWORDS) for text in texts)
    bearish_hits = sum(_count_hits(text, BEARISH_KEYWORDS) for text in texts)
    neutral_hits = sum(_count_hits(text, NEUTRAL_KEYWORDS) for text in texts)
    total_directional = bullish_hits + bearish_hits
    if total_directional == 0:
        net_score = 0.0
    else:
        net_score = (bullish_hits - bearish_hits) / total_directional
    # More directional evidence => slightly higher base confidence.
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
    confidence = max(
        0.50,
        min(
            0.90,
            snapshot.confidence_base + abs(snapshot.net_score) * 0.20,
        ),
    )
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
def _fetch_finnhub_news_texts(
    symbol: str,
    from_date: str,
    to_date: str,
    max_items: int,
) -> list[str]:
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        return []
    url = "https://finnhub.io/api/v1/company-news"
    params = {
        "symbol": symbol,
        "from": from_date,
        "to": to_date,
        "token": api_key,
    }
    with httpx.Client(timeout=8.0) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        payload = response.json()
    if not isinstance(payload, list):
        return []
    texts: list[str] = []
    for item in payload[:max_items]:
        if not isinstance(item, dict):
            continue
        headline = str(item.get("headline", "")).strip()
        summary = str(item.get("summary", "")).strip()
        joined = " ".join(part for part in [headline, summary] if part)
        if joined:
            texts.append(joined)
    return texts
def _fetch_yfinance_news_texts(symbol: str, max_items: int) -> list[str]:
    ticker = yf.Ticker(symbol)
    raw_news = getattr(ticker, "news", None)
    if not isinstance(raw_news, list):
        return []
    texts: list[str] = []
    for item in raw_news[:max_items]:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", "")).strip()
        summary = str(item.get("summary", "")).strip()
        joined = " ".join(part for part in [title, summary] if part)
        if joined:
            texts.append(joined)
    return texts
def fetch_sentiment_texts(
    symbol: str,
    query: str,
    lookback_days: int = 7,
    max_news_items: int = 20,
) -> tuple[list[str], str, int]:
    """
    Returns:
    - texts corpus (query included as first element)
    - source label
    - number of external news items
    """
    now = datetime.now(timezone.utc).date()
    from_date = (now - timedelta(days=lookback_days)).isoformat()
    to_date = now.isoformat()
    news_texts: list[str] = []
    source = "query_only"
    try:
        news_texts = _fetch_finnhub_news_texts(
            symbol=symbol,
            from_date=from_date,
            to_date=to_date,
            max_items=max_news_items,
        )
        if news_texts:
            source = "finnhub"
    except Exception:
        news_texts = []
    if not news_texts:
        try:
            news_texts = _fetch_yfinance_news_texts(symbol=symbol, max_items=max_news_items)
            if news_texts:
                source = "yfinance_news"
        except Exception:
            news_texts = []
    corpus = [query.strip()] + news_texts if query.strip() else news_texts
    if not corpus:
        corpus = [f"{symbol} sentiment unavailable"]
    return corpus, source, len(news_texts)
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
    snapshot = _build_sentiment_snapshot_from_texts(texts)
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