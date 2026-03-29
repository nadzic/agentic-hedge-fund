from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

import httpx
import yfinance as yf
from dotenv import load_dotenv

_ = load_dotenv()


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
    now = datetime.now(UTC).date()
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
