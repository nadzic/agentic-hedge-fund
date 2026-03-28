from __future__ import annotations

import pandas as pd
import yfinance as yf


def _timeframe_from_horizon(horizon: str) -> tuple[str, str]:
    if horizon == "intraday":
        return "60d", "1h"
    if horizon == "position":
        return "2y", "1d"
    return "1y", "1d"


def download_ohlcv(symbol: str, horizon: str) -> pd.DataFrame:
    period, interval = _timeframe_from_horizon(horizon)
    raw_frame = yf.download(
        tickers=symbol,
        period=period,
        interval=interval,
        auto_adjust=False,
        progress=False,
    )
    if raw_frame is None or raw_frame.empty:
        raise ValueError(f"No market data returned for symbol={symbol}.")
    frame = raw_frame

    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = [str(col[0]) for col in frame.columns]

    required = {"Open", "High", "Low", "Close", "Volume"}
    missing = required - set(str(column) for column in frame.columns)
    if missing:
        raise ValueError(f"Missing OHLCV columns: {sorted(missing)}")

    frame = frame.dropna(subset=["Close"]).copy()
    if len(frame) < 220:
        raise ValueError(f"Not enough data points ({len(frame)}) for EMA200/indicators.")
    return frame
