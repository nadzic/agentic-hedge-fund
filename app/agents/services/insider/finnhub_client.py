from __future__ import annotations

import os
import re
from datetime import date, timedelta

import httpx
from dotenv import load_dotenv

load_dotenv()
_TICKER_PATTERN = re.compile(r"^[A-Z]{1,5}$")


def fetch_insider_transactions(
    symbol: str, lookback_days: int = 30
) -> list[dict[str, object]]:
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        return []

    to_dt = date.today()
    from_dt = to_dt - timedelta(days=lookback_days)

    url = "https://finnhub.io/api/v1/stock/insider-transactions"
    params = {
        "symbol": symbol.upper().strip(),
        "from": from_dt.isoformat(),
        "to": to_dt.isoformat(),
        "token": api_key,
    }

    with httpx.Client(timeout=10.0) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        payload = response.json()

    if not isinstance(payload, dict):
        return []

    data = payload.get("data", [])
    if not isinstance(data, list):
        return []

    cleaned: list[dict[str, object]] = []
    for row in data:
        if isinstance(row, dict):
            cleaned.append({str(key): value for key, value in row.items()})
    return cleaned


def search_symbol_by_company_name(query: str) -> str | None:
    normalized_query = query.strip()
    if not normalized_query:
        return None

    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        return None

    url = "https://finnhub.io/api/v1/search"
    params = {
        "q": normalized_query,
        "token": api_key,
    }

    try:
        with httpx.Client(timeout=2.5) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()
    except Exception:
        return None

    if not isinstance(payload, dict):
        return None

    results = payload.get("result")
    if not isinstance(results, list):
        return None

    for item in results:
        if not isinstance(item, dict):
            continue
        symbol = str(item.get("symbol") or item.get("displaySymbol") or "").strip().upper()
        if _TICKER_PATTERN.match(symbol):
            return symbol

    return None