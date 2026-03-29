from __future__ import annotations

import os
from datetime import date, timedelta

import httpx
from dotenv import load_dotenv

load_dotenv()


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