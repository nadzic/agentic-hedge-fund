from __future__ import annotations

from typing import cast

import pandas as pd

from app.agents.services.technicals.types import TechnicalSnapshot


def _compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = cast(pd.Series, close.diff())
    gain = cast(pd.Series, delta.clip(lower=0.0))
    loss = cast(pd.Series, -delta.clip(upper=0.0))
    avg_gain = cast(pd.Series, gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean())
    avg_loss = cast(pd.Series, loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean())
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    rsi_values = 100 - (100 / (1 + rs))
    rsi = pd.Series(rsi_values, index=close.index)
    return cast(pd.Series, rsi.fillna(50.0))


def compute_indicators(frame: pd.DataFrame) -> TechnicalSnapshot:
    close = cast(pd.Series, frame["Close"]).astype(float)
    ema12 = cast(pd.Series, close.ewm(span=12, adjust=False).mean())
    ema26 = cast(pd.Series, close.ewm(span=26, adjust=False).mean())
    macd = cast(pd.Series, ema12 - ema26)
    macd_signal = cast(pd.Series, macd.ewm(span=9, adjust=False).mean())
    macd_hist = cast(pd.Series, macd - macd_signal)
    ema200 = cast(pd.Series, close.ewm(span=200, adjust=False).mean())
    bb_mid = cast(pd.Series, close.rolling(window=20, min_periods=20).mean())
    bb_std = cast(pd.Series, close.rolling(window=20, min_periods=20).std(ddof=0))
    bb_upper = cast(pd.Series, bb_mid + 2 * bb_std)
    bb_lower = cast(pd.Series, bb_mid - 2 * bb_std)
    rsi14 = _compute_rsi(close, period=14)

    return TechnicalSnapshot(
        close=float(close.iloc[-1]),
        rsi14=float(rsi14.iloc[-1]),
        macd=float(macd.iloc[-1]),
        macd_signal=float(macd_signal.iloc[-1]),
        macd_hist=float(macd_hist.iloc[-1]),
        ema200=float(ema200.iloc[-1]),
        bb_upper=float(bb_upper.iloc[-1]),
        bb_mid=float(bb_mid.iloc[-1]),
        bb_lower=float(bb_lower.iloc[-1]),
    )
